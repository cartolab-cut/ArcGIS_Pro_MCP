"""Raster, terrain, and surface analysis tools for ArcGIS Pro MCP Server."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..models import (
    CalculateAspectRequest,
    CalculateSlopeRequest,
    CreateContoursRequest,
    CreateHillshadeRequest,
    DescribeRasterRequest,
    ExtractRasterByMaskRequest,
)
from ..services.raster_service import RasterService
from ..utils import arcpy_safe


@arcpy_safe
def describe_raster(raster_path: str) -> Dict[str, Any]:
    """Retrieves metadata, band count, cell dimensions, pixel type, and statistics for a raster.

    Parameters:
        raster_path: Path to raster file (.tif, .img, GDB raster, etc.).
    """
    req = DescribeRasterRequest(raster_path=raster_path)
    return RasterService.describe_raster(req.raster_path)


@arcpy_safe
def create_hillshade(
    in_elevation_raster: str,
    out_raster: str,
    azimuth: float = 315.0,
    altitude: float = 45.0,
    model_shadows: str = "NO_SHADOWS",
    z_factor: float = 1.0,
) -> Dict[str, Any]:
    """Generates a shaded relief (hillshade) raster from an elevation surface.

    Requires Spatial Analyst or 3D Analyst extension.

    Parameters:
        in_elevation_raster: Path to elevation DEM raster.
        out_raster: Destination path for hillshade raster.
        azimuth: Angular direction of sun (0-360, default: 315).
        altitude: Angle of illumination source above horizon (0-90, default: 45).
        model_shadows: 'NO_SHADOWS' or 'SHADOWS'.
        z_factor: Elevation scale factor.
    """
    req = CreateHillshadeRequest(
        in_dem=in_elevation_raster,
        out_raster=out_raster,
        azimuth=azimuth,
        altitude=altitude,
        z_factor=z_factor,
    )
    return RasterService.create_hillshade(
        in_elevation_raster=req.in_dem,
        out_raster=req.out_raster,
        azimuth=req.azimuth,
        altitude=req.altitude,
        model_shadows=model_shadows,
        z_factor=req.z_factor,
    )


@arcpy_safe
def calculate_slope(
    in_elevation_raster: str,
    out_raster: str,
    output_measurement: str = "DEGREE",
    z_factor: float = 1.0,
) -> Dict[str, Any]:
    """Calculates the slope (rate of maximum change in z-value) from an elevation raster.

    Parameters:
        in_elevation_raster: DEM raster path.
        out_raster: Destination slope raster path.
        output_measurement: 'DEGREE' or 'PERCENT_RISE'.
        z_factor: Elevation vertical scaling factor.
    """
    req = CalculateSlopeRequest(
        in_dem=in_elevation_raster,
        out_raster=out_raster,
        output_measurement=output_measurement,
        z_factor=z_factor,
    )
    return RasterService.calculate_slope(
        in_elevation_raster=req.in_dem,
        out_raster=req.out_raster,
        output_measurement=req.output_measurement,
        z_factor=req.z_factor,
    )


@arcpy_safe
def calculate_aspect(
    in_elevation_raster: str,
    out_raster: str,
    method: str = "PLANAR",
) -> Dict[str, Any]:
    """Calculates the aspect (compass direction the downhill slope faces) for each raster cell.

    Parameters:
        in_elevation_raster: DEM raster path.
        out_raster: Destination aspect raster path.
        method: 'PLANAR' or 'GEODESIC'.
    """
    req = CalculateAspectRequest(
        in_dem=in_elevation_raster,
        out_raster=out_raster,
        method=method,
    )
    return RasterService.calculate_aspect(
        in_elevation_raster=req.in_dem,
        out_raster=req.out_raster,
        method=req.method,
    )


@arcpy_safe
def create_contours(
    in_elevation_raster: str,
    out_feature_class: str,
    contour_interval: float = 10.0,
    base_contour: float = 0.0,
    z_factor: float = 1.0,
) -> Dict[str, Any]:
    """Creates contour lines of elevation from a raster surface.

    Parameters:
        in_elevation_raster: DEM raster path.
        out_feature_class: Destination contour polyline feature class.
        contour_interval: Elevation difference between contour lines.
        base_contour: Base elevation starting point.
        z_factor: Vertical scaling factor.
    """
    req = CreateContoursRequest(
        in_dem=in_elevation_raster,
        out_feature_class=out_feature_class,
        interval=contour_interval,
        base_contour=base_contour,
        z_factor=z_factor,
    )
    return RasterService.create_contours(
        in_elevation_raster=req.in_dem,
        out_feature_class=req.out_feature_class,
        contour_interval=req.interval,
        base_contour=req.base_contour,
        z_factor=req.z_factor,
    )


@arcpy_safe
def extract_raster_by_mask(
    in_raster: str,
    mask_data: str,
    out_raster: str,
) -> Dict[str, Any]:
    """Extracts the cells of a raster corresponding to the area defined by a mask polygon or raster.

    Parameters:
        in_raster: Input raster to clip.
        mask_data: Polygon feature class or raster mask.
        out_raster: Output extracted raster path.
    """
    req = ExtractRasterByMaskRequest(
        in_raster=in_raster,
        in_mask_data=mask_data,
        out_raster=out_raster,
    )
    return RasterService.extract_raster_by_mask(
        in_raster=req.in_raster,
        mask_data=req.in_mask_data,
        out_raster=req.out_raster,
    )
