"""Attribute queries, selections, and analytical statistics service for ArcGIS Pro."""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
import arcpy

from ..utils import capture_arcpy_messages, sanitize_path


class AnalysisService:
    """Service layer encapsulating attribute querying, cursors, selection, and statistics."""

    @staticmethod
    def query_features(
        feature_class: str,
        where_clause: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        include_geometry_wkt: bool = False,
    ) -> Dict[str, Any]:
        """Queries features from a feature class or table using an SQL WHERE clause."""
        clean_fc = sanitize_path(feature_class)
        if not arcpy.Exists(clean_fc):
            return {"success": False, "error": f"Dataset not found: {clean_fc}"}

        desc = arcpy.da.Describe(clean_fc)
        all_field_names = [f.name for f in desc.get("fields", []) if f.type not in ("Geometry", "Raster", "Blob")]

        target_fields = []
        if fields:
            for f in fields:
                if f in all_field_names:
                    target_fields.append(f)
        else:
            target_fields = all_field_names

        cursor_fields = list(target_fields)
        has_geom = desc.get("shapeType") not in (None, "", "Unknown") and include_geometry_wkt
        if has_geom:
            cursor_fields.append("SHAPE@WKT")

        max_limit = min(max(1, limit), 1000)
        rows_data = []
        total_matching = 0

        with arcpy.da.SearchCursor(clean_fc, cursor_fields, where_clause=where_clause or None) as cursor:
            for idx, row in enumerate(cursor):
                total_matching += 1
                if idx < offset:
                    continue
                if len(rows_data) < max_limit:
                    row_dict = {}
                    for f_idx, f_name in enumerate(target_fields):
                        val = row[f_idx]
                        if hasattr(val, "isoformat"):
                            val = val.isoformat()
                        row_dict[f_name] = val
                    if has_geom:
                        row_dict["geometry_wkt"] = row[-1]
                    rows_data.append(row_dict)

        return {
            "success": True,
            "feature_class": clean_fc,
            "where_clause": where_clause,
            "returned_count": len(rows_data),
            "total_matched_in_scan": total_matching,
            "offset": offset,
            "fields": target_fields,
            "records": rows_data,
        }

    @staticmethod
    def calculate_field(
        in_table: str,
        field: str,
        expression: str,
        expression_type: str = "PYTHON3",
        code_block: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates or populates values of a field in a feature class or table using Python."""
        clean_table = sanitize_path(in_table)
        arcpy.management.CalculateField(
            in_table=clean_table,
            field=field,
            expression=expression,
            expression_type=expression_type,
            code_block=code_block or "",
        )
        return {
            "success": True,
            "message": f"Successfully calculated field '{field}' on {clean_table}",
            "expression": expression,
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def select_features_by_attribute(
        in_layer: str,
        out_feature_class: str,
        where_clause: str,
    ) -> Dict[str, Any]:
        """Selects features using an SQL WHERE clause and writes them to a new feature class."""
        clean_in = sanitize_path(in_layer)
        clean_out = sanitize_path(out_feature_class)

        arcpy.analysis.Select(
            in_features=clean_in,
            out_feature_class=clean_out,
            where_clause=where_clause,
        )
        count = int(arcpy.management.GetCount(clean_out)[0])
        return {
            "success": True,
            "message": f"Selected {count} features matching '{where_clause}'",
            "output_feature_class": clean_out,
            "feature_count": count,
        }

    @staticmethod
    def select_features_by_location(
        target_layer: str,
        selecting_features: str,
        out_feature_class: str,
        overlap_type: str = "INTERSECT",
        search_distance: Optional[str] = None,
        invert_spatial_relationship: bool = False,
    ) -> Dict[str, Any]:
        """Selects features based on their spatial relationship with another dataset."""
        clean_target = sanitize_path(target_layer)
        clean_select = sanitize_path(selecting_features)
        clean_out = sanitize_path(out_feature_class)

        temp_layer = "temp_select_layer"
        if arcpy.Exists(temp_layer):
            arcpy.management.Delete(temp_layer)

        arcpy.management.MakeFeatureLayer(clean_target, temp_layer)
        try:
            arcpy.management.SelectLayerByLocation(
                in_layer=temp_layer,
                overlap_type=str(overlap_type),
                select_features=clean_select,
                search_distance=search_distance or "",
                selection_type="NEW_SELECTION",
                invert_spatial_relationship="INVERT" if invert_spatial_relationship else "NOT_INVERT",
            )
            arcpy.management.CopyFeatures(temp_layer, clean_out)
            count = int(arcpy.management.GetCount(clean_out)[0])

            return {
                "success": True,
                "message": f"Spatial selection created {clean_out} with {count} features.",
                "output_feature_class": clean_out,
                "feature_count": count,
                "relationship": str(overlap_type),
            }
        finally:
            arcpy.management.Delete(temp_layer)

    @staticmethod
    def get_summary_statistics(
        in_table: str,
        statistics_fields: List[List[str]],
        case_fields: Optional[List[str]] = None,
        out_table: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates summary statistics (SUM, MEAN, MIN, MAX, STD, COUNT).

        Uses high-speed 'memory/' workspace if out_table is omitted.
        """
        clean_table = sanitize_path(in_table)
        if out_table:
            clean_out = sanitize_path(out_table)
            is_memory = False
        else:
            clean_out = "memory/temp_stats_tbl"
            is_memory = True

        if is_memory and arcpy.Exists(clean_out):
            arcpy.management.Delete(clean_out)

        try:
            arcpy.analysis.Statistics(
                in_table=clean_table,
                out_table=clean_out,
                statistics_fields=statistics_fields,
                case_field=case_fields or [],
            )

            desc = arcpy.da.Describe(clean_out)
            field_names = [f.name for f in desc["fields"] if f.type not in ("OID", "Geometry")]

            records = []
            with arcpy.da.SearchCursor(clean_out, field_names) as cur:
                for row in cur:
                    records.append(dict(zip(field_names, row)))

            return {
                "success": True,
                "input_table": clean_table,
                "output_table": clean_out,
                "statistics": records,
            }
        finally:
            if is_memory and arcpy.Exists(clean_out):
                try:
                    arcpy.management.Delete(clean_out)
                except Exception:
                    pass
