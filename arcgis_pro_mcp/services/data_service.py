"""Data management and geodatabase service for ArcGIS Pro."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import arcpy

from ..utils import (
    capture_arcpy_messages,
    format_extent,
    format_spatial_reference,
    sanitize_path,
)


class DataManagementService:
    """Service layer encapsulating dataset, schema, and geodatabase operations."""

    @staticmethod
    def create_file_gdb(out_folder_path: str, gdb_name: str) -> Dict[str, Any]:
        """Creates a new File Geodatabase (.gdb) in the specified folder."""
        clean_folder = sanitize_path(out_folder_path)
        os.makedirs(clean_folder, exist_ok=True)

        name = gdb_name.strip()
        if not name.lower().endswith(".gdb"):
            name = f"{name}.gdb"

        gdb_path = os.path.join(clean_folder, name)
        if os.path.exists(gdb_path):
            return {
                "success": True,
                "message": f"Geodatabase already exists at: {gdb_path}",
                "gdb_path": gdb_path,
            }

        arcpy.management.CreateFileGDB(clean_folder, name)
        return {
            "success": True,
            "message": f"File Geodatabase successfully created at {gdb_path}",
            "gdb_path": gdb_path,
        }

    @staticmethod
    def create_feature_class(
        out_path: str,
        out_name: str,
        geometry_type: str = "POLYGON",
        spatial_reference_wkid: int = 4326,
        has_m: str = "DISABLED",
        has_z: str = "DISABLED",
    ) -> Dict[str, Any]:
        """Creates an empty feature class in a geodatabase or folder."""
        clean_out = sanitize_path(out_path)
        sr = arcpy.SpatialReference(spatial_reference_wkid)

        arcpy.management.CreateFeatureclass(
            out_path=clean_out,
            out_name=out_name,
            geometry_type=str(geometry_type).upper(),
            spatial_reference=sr,
            has_m=has_m,
            has_z=has_z,
        )
        full_path = os.path.join(clean_out, out_name)

        return {
            "success": True,
            "message": f"Created feature class: {out_name}",
            "feature_class_path": full_path,
            "geometry_type": str(geometry_type).upper(),
            "spatial_reference": format_spatial_reference(sr),
        }

    @staticmethod
    def list_gdb_contents(gdb_path: str) -> Dict[str, Any]:
        """Catalogs feature classes, tables, feature datasets, and rasters in a GDB."""
        clean_gdb = sanitize_path(gdb_path)
        if not os.path.exists(clean_gdb):
            return {"success": False, "error": f"Geodatabase does not exist: {clean_gdb}"}

        prev_ws = arcpy.env.workspace
        try:
            arcpy.env.workspace = clean_gdb

            feature_datasets = arcpy.ListDatasets(feature_type="feature") or []
            standalone_fc = arcpy.ListFeatureClasses() or []
            tables = arcpy.ListTables() or []
            rasters = arcpy.ListRasters() or []

            datasets_info = []
            for fds in feature_datasets:
                arcpy.env.workspace = os.path.join(clean_gdb, fds)
                fds_fcs = arcpy.ListFeatureClasses() or []
                datasets_info.append({
                    "dataset_name": fds,
                    "feature_classes": fds_fcs,
                })
                arcpy.env.workspace = clean_gdb

            return {
                "success": True,
                "gdb_path": clean_gdb,
                "feature_datasets": datasets_info,
                "standalone_feature_classes": standalone_fc,
                "tables": tables,
                "rasters": rasters,
                "total_items": len(feature_datasets) + len(standalone_fc) + len(tables) + len(rasters),
            }
        finally:
            arcpy.env.workspace = prev_ws

    @staticmethod
    def describe_dataset(dataset_path: str) -> Dict[str, Any]:
        """Returns comprehensive schema, fields, extent, and geometry metadata."""
        clean_path = sanitize_path(dataset_path)
        if not arcpy.Exists(clean_path):
            return {"success": False, "error": f"Dataset does not exist: {clean_path}"}

        desc = arcpy.da.Describe(clean_path)
        data_type = desc.get("dataType", "Unknown")
        result: Dict[str, Any] = {
            "success": True,
            "path": clean_path,
            "name": desc.get("name"),
            "data_type": data_type,
        }

        if "spatialReference" in desc and desc["spatialReference"]:
            result["spatial_reference"] = format_spatial_reference(desc["spatialReference"])

        if "extent" in desc and desc["extent"]:
            result["extent"] = format_extent(desc["extent"])

        if "shapeType" in desc:
            result["shape_type"] = desc.get("shapeType")

        if "fields" in desc:
            fields = []
            for f in desc["fields"]:
                fields.append({
                    "name": f.name,
                    "type": f.type,
                    "length": f.length,
                    "alias": f.aliasName,
                    "editable": f.editable,
                    "nullable": f.isNullable,
                })
            result["fields"] = fields

        try:
            if data_type in ("FeatureClass", "Table", "ShapeFile"):
                result["record_count"] = int(arcpy.management.GetCount(clean_path)[0])
        except Exception:
            pass

        return result

    @staticmethod
    def export_dataset(
        in_data: str,
        out_data: str,
        where_clause: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exports or converts datasets between formats."""
        clean_in = sanitize_path(in_data)
        clean_out = sanitize_path(out_data)

        os.makedirs(os.path.dirname(os.path.abspath(clean_out)), exist_ok=True)

        if clean_out.lower().endswith(".geojson") or clean_out.lower().endswith(".json"):
            arcpy.conversion.FeaturesToJSON(
                in_features=clean_in,
                out_json_file=clean_out,
                format_json=True,
                geoJSON=True,
                where_clause=where_clause or "",
            )
        else:
            arcpy.conversion.ExportFeatures(
                in_features=clean_in,
                out_features=clean_out,
                where_clause=where_clause or "",
            )

        count = int(arcpy.management.GetCount(clean_out)[0])
        return {
            "success": True,
            "message": f"Exported to {clean_out}",
            "output_path": clean_out,
            "feature_count": count,
        }

    @staticmethod
    def add_field(
        in_table: str,
        field_name: str,
        field_type: str = "TEXT",
        field_length: int = 255,
        field_alias: Optional[str] = None,
        field_is_nullable: bool = True,
    ) -> Dict[str, Any]:
        """Adds a new column / field to a feature class or table."""
        clean_table = sanitize_path(in_table)
        arcpy.management.AddField(
            in_table=clean_table,
            field_name=field_name,
            field_type=str(field_type).upper(),
            field_length=field_length,
            field_alias=field_alias or field_name,
            field_is_nullable="NULLABLE" if field_is_nullable else "NON_NULLABLE",
        )
        return {
            "success": True,
            "message": f"Field '{field_name}' ({str(field_type).upper()}) added successfully to {clean_table}",
        }

    @staticmethod
    def delete_dataset(target_data: str) -> Dict[str, Any]:
        """Safely deletes a dataset from disk or geodatabase."""
        clean_path = sanitize_path(target_data)
        if not arcpy.Exists(clean_path):
            return {"success": False, "error": f"Target dataset does not exist: {clean_path}"}

        arcpy.management.Delete(clean_path)
        return {
            "success": True,
            "message": f"Successfully deleted {clean_path}",
        }
