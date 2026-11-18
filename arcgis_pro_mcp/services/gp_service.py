"""Geoprocessing and spatial analysis service for ArcGIS Pro."""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
import arcpy

from ..utils import capture_arcpy_messages, sanitize_path


class GeoprocessingService:
    """Service layer encapsulating ArcPy geoprocessing tools."""

    @staticmethod
    def run_geoprocessing_tool(
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dynamically executes any ArcPy geoprocessing tool by name."""
        args = arguments or {}
        cleaned_args = {}
        for k, v in args.items():
            if isinstance(v, str) and (":" in v or "\\" in v or "/" in v):
                cleaned_args[k] = sanitize_path(v)
            elif isinstance(v, list):
                cleaned_args[k] = [sanitize_path(i) if isinstance(i, str) else i for i in v]
            else:
                cleaned_args[k] = v

        func = None
        if hasattr(arcpy, tool_name):
            func = getattr(arcpy, tool_name)
        elif hasattr(arcpy.gp, tool_name):
            func = getattr(arcpy.gp, tool_name)
        elif "_" in tool_name:
            base, tbox = tool_name.split("_", 1)
            if hasattr(arcpy, tbox) and hasattr(getattr(arcpy, tbox), base):
                func = getattr(getattr(arcpy, tbox), base)

        if func is None:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' could not be located in arcpy.",
            }

        start_time = time.time()
        result = func(**cleaned_args)
        duration = round(time.time() - start_time, 2)
        messages = capture_arcpy_messages()

        return {
            "success": True,
            "tool_name": tool_name,
            "execution_time_seconds": duration,
            "result": str(result) if result is not None else "Completed",
            "messages": messages,
        }

    @staticmethod
    def buffer_analysis(
        in_features: str,
        out_feature_class: str,
        buffer_distance_or_field: str,
        line_side: str = "FULL",
        line_end_type: str = "ROUND",
        dissolve_option: str = "NONE",
    ) -> Dict[str, Any]:
        """Creates buffer polygons around input features."""
        clean_in = sanitize_path(in_features)
        clean_out = sanitize_path(out_feature_class)

        start = time.time()
        arcpy.analysis.Buffer(
            in_features=clean_in,
            out_feature_class=clean_out,
            buffer_distance_or_field=buffer_distance_or_field,
            line_side=line_side,
            line_end_type=line_end_type,
            dissolve_option=dissolve_option,
        )
        count = int(arcpy.management.GetCount(clean_out)[0])

        return {
            "success": True,
            "message": f"Buffer analysis created {clean_out} with {count} features.",
            "output_feature_class": clean_out,
            "feature_count": count,
            "buffer_distance": buffer_distance_or_field,
            "duration_seconds": round(time.time() - start, 2),
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def clip_analysis(
        in_features: str,
        clip_features: str,
        out_feature_class: str,
        cluster_tolerance: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Clips input features using a boundary dataset."""
        clean_in = sanitize_path(in_features)
        clean_clip = sanitize_path(clip_features)
        clean_out = sanitize_path(out_feature_class)

        start = time.time()
        arcpy.analysis.Clip(
            in_features=clean_in,
            clip_features=clean_clip,
            out_feature_class=clean_out,
            cluster_tolerance=cluster_tolerance or "",
        )
        count = int(arcpy.management.GetCount(clean_out)[0])

        return {
            "success": True,
            "message": f"Clip analysis produced {count} features at {clean_out}",
            "output_feature_class": clean_out,
            "feature_count": count,
            "duration_seconds": round(time.time() - start, 2),
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def intersect_analysis(
        in_features: List[str],
        out_feature_class: str,
        join_attributes: str = "ALL",
        cluster_tolerance: Optional[str] = None,
        output_type: str = "INPUT",
    ) -> Dict[str, Any]:
        """Calculates the geometric intersection of multiple feature classes."""
        clean_inputs = [sanitize_path(f) for f in in_features]
        clean_out = sanitize_path(out_feature_class)

        start = time.time()
        arcpy.analysis.Intersect(
            in_features=clean_inputs,
            out_feature_class=clean_out,
            join_attributes=join_attributes,
            cluster_tolerance=cluster_tolerance or "",
            output_type=output_type,
        )
        count = int(arcpy.management.GetCount(clean_out)[0])

        return {
            "success": True,
            "message": f"Intersect created {clean_out} containing {count} features.",
            "output_feature_class": clean_out,
            "feature_count": count,
            "duration_seconds": round(time.time() - start, 2),
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def spatial_join(
        target_features: str,
        join_features: str,
        out_feature_class: str,
        join_operation: str = "JOIN_ONE_TO_ONE",
        join_type: str = "KEEP_ALL",
        match_option: str = "INTERSECT",
        search_radius: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Joins attributes from one feature layer to another based on spatial relationships."""
        clean_target = sanitize_path(target_features)
        clean_join = sanitize_path(join_features)
        clean_out = sanitize_path(out_feature_class)

        start = time.time()
        arcpy.analysis.SpatialJoin(
            target_features=clean_target,
            join_features=clean_join,
            out_feature_class=clean_out,
            join_operation=join_operation,
            join_type=join_type,
            match_option=match_option,
            search_radius=search_radius or "",
        )
        count = int(arcpy.management.GetCount(clean_out)[0])

        return {
            "success": True,
            "message": f"Spatial join generated {clean_out} with {count} features.",
            "output_feature_class": clean_out,
            "feature_count": count,
            "duration_seconds": round(time.time() - start, 2),
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def dissolve_features(
        in_features: str,
        out_feature_class: str,
        dissolve_fields: Optional[List[str]] = None,
        statistics_fields: Optional[List[List[str]]] = None,
        multi_part: bool = True,
    ) -> Dict[str, Any]:
        """Aggregates features that have the same attribute values."""
        clean_in = sanitize_path(in_features)
        clean_out = sanitize_path(out_feature_class)

        start = time.time()
        arcpy.management.Dissolve(
            in_features=clean_in,
            out_feature_class=clean_out,
            dissolve_field=dissolve_fields or [],
            statistics_fields=statistics_fields or [],
            multi_part="MULTI_PART" if multi_part else "SINGLE_PART",
        )
        count = int(arcpy.management.GetCount(clean_out)[0])

        return {
            "success": True,
            "message": f"Dissolve produced {count} aggregate features at {clean_out}",
            "output_feature_class": clean_out,
            "feature_count": count,
            "duration_seconds": round(time.time() - start, 2),
            "geoprocessing_messages": capture_arcpy_messages(),
        }
