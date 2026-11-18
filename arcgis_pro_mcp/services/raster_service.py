"""Raster, surface, and terrain analysis service for ArcGIS Pro."""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
import arcpy

from ..utils import (
    capture_arcpy_messages,
    extension_scope,
    format_extent,
    format_spatial_reference,
    sanitize_path,
)


class RasterService:
    """Service layer encapsulating DEM, surface, and raster processing."""

    @staticmethod
    def describe_raster(raster_path: str) -> Dict[str, Any]:
        """Retrieves metadata, band count, cell dimensions, and statistics."""
        clean_path = sanitize_path(raster_path)
        if not arcpy.Exists(clean_path):
            return {"success": False, "error": f"Raster not found: {clean_path}"}

        desc = arcpy.da.Describe(clean_path)
        raster_obj = arcpy.Raster(clean_path)

        stats = {}
        try:
            stats["mean"] = float(raster_obj.mean) if raster_obj.mean is not None else None
            stats["standard_deviation"] = (
                float(raster_obj.standardDeviation)
                if raster_obj.standardDeviation is not None
                else None
            )
            stats["minimum"] = float(raster_obj.minimum) if raster_obj.minimum is not None else None
            stats["maximum"] = float(raster_obj.maximum) if raster_obj.maximum is not None else None
        except Exception:
            pass

        res = {
            "success": True,
            "raster_path": clean_path,
            "format": desc.get("format", "Unknown"),
            "band_count": raster_obj.bandCount,
            "width_pixels": raster_obj.width,
            "height_pixels": raster_obj.height,
            "cell_size_x": raster_obj.meanCellWidth,
            "cell_size_y": raster_obj.meanCellHeight,
            "pixel_type": raster_obj.pixelType,
            "no_data_value": raster_obj.noDataValue,
            "extent": format_extent(raster_obj.extent),
            "spatial_reference": format_spatial_reference(raster_obj.spatialReference),
            "statistics": stats,
        }
        del raster_obj
        return res

    @staticmethod
    def create_hillshade(
        in_elevation_raster: str,
        out_raster: str,
        azimuth: float = 315.0,
        altitude: float = 45.0,
        model_shadows: str = "NO_SHADOWS",
        z_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Generates a shaded relief (hillshade) raster."""
        clean_in = sanitize_path(in_elevation_raster)
        clean_out = sanitize_path(out_raster)

        with extension_scope("Spatial", "3D"):
            arcpy.ddd.HillShade(
                in_raster=clean_in,
                out_raster=clean_out,
                azimuth=azimuth,
                altitude=altitude,
                model_shadows=model_shadows,
                z_factor=z_factor,
            )

        return {
            "success": True,
            "message": f"Hillshade successfully generated at {clean_out}",
            "out_raster": clean_out,
            "azimuth": azimuth,
            "altitude": altitude,
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def calculate_slope(
        in_elevation_raster: str,
        out_raster: str,
        output_measurement: str = "DEGREE",
        z_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Calculates the slope from an elevation raster."""
        clean_in = sanitize_path(in_elevation_raster)
        clean_out = sanitize_path(out_raster)

        with extension_scope("Spatial", "3D"):
            arcpy.ddd.Slope(
                in_raster=clean_in,
                out_raster=clean_out,
                output_measurement=str(output_measurement).upper(),
                z_factor=z_factor,
            )

        return {
            "success": True,
            "message": f"Slope raster generated at {clean_out}",
            "out_raster": clean_out,
            "output_measurement": str(output_measurement).upper(),
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def calculate_aspect(
        in_elevation_raster: str,
        out_raster: str,
        method: str = "PLANAR",
    ) -> Dict[str, Any]:
        """Calculates downhill slope aspect for each raster cell."""
        clean_in = sanitize_path(in_elevation_raster)
        clean_out = sanitize_path(out_raster)

        with extension_scope("Spatial", "3D"):
            arcpy.ddd.Aspect(
                in_raster=clean_in,
                out_raster=clean_out,
                method=str(method),
            )

        return {
            "success": True,
            "message": f"Aspect raster generated at {clean_out}",
            "out_raster": clean_out,
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def create_contours(
        in_elevation_raster: str,
        out_feature_class: str,
        contour_interval: float = 10.0,
        base_contour: float = 0.0,
        z_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Creates contour lines of elevation from a raster surface."""
        clean_in = sanitize_path(in_elevation_raster)
        clean_out = sanitize_path(out_feature_class)

        with extension_scope("Spatial", "3D"):
            arcpy.ddd.Contour(
                in_raster=clean_in,
                out_polyline_features=clean_out,
                contour_interval=contour_interval,
                base_contour=base_contour,
                z_factor=z_factor,
            )

        count = int(arcpy.management.GetCount(clean_out)[0])
        return {
            "success": True,
            "message": f"Generated {count} contour lines with interval {contour_interval}",
            "out_feature_class": clean_out,
            "contour_count": count,
            "contour_interval": contour_interval,
        }

    @staticmethod
    def extract_raster_by_mask(
        in_raster: str,
        mask_data: str,
        out_raster: str,
    ) -> Dict[str, Any]:
        """Extracts cells of a raster corresponding to a mask boundary."""
        clean_in = sanitize_path(in_raster)
        clean_mask = sanitize_path(mask_data)
        clean_out = sanitize_path(out_raster)

        with extension_scope("Spatial") as status:
            if status == "Spatial" or status == "Available":
                from arcpy.sa import ExtractByMask
                out_extracted = ExtractByMask(clean_in, clean_mask)
                out_extracted.save(clean_out)
            else:
                arcpy.management.Clip(
                    in_raster=clean_in,
                    out_raster=clean_out,
                    in_template_dataset=clean_mask,
                    clipping_geometry="ClippingGeometry",
                )

        return {
            "success": True,
            "message": f"Extracted raster saved to {clean_out}",
            "out_raster": clean_out,
            "geoprocessing_messages": capture_arcpy_messages(),
        }
