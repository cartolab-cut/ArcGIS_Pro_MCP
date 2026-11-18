"""Data management and geodatabase tools for ArcGIS Pro MCP Server."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..models import (
    AddFieldRequest,
    CreateFeatureClassRequest,
    CreateFileGDBRequest,
    DeleteDatasetRequest,
    DescribeDatasetRequest,
    ExportDatasetRequest,
    ListGDBContentsRequest,
)
from ..services.data_service import DataManagementService
from ..utils import arcpy_safe


@arcpy_safe
def create_file_gdb(
    out_folder_path: str,
    gdb_name: str,
) -> Dict[str, Any]:
    """Creates a new File Geodatabase (.gdb) in the specified folder.

    Parameters:
        out_folder_path: Folder where the geodatabase will be created.
        gdb_name: Name of the geodatabase (with or without .gdb extension).
    """
    req = CreateFileGDBRequest(
        out_folder_path=out_folder_path,
        gdb_name=gdb_name,
    )
    return DataManagementService.create_file_gdb(
        out_folder_path=req.out_folder_path,
        gdb_name=req.gdb_name,
    )


@arcpy_safe
def create_feature_class(
    out_path: str,
    out_name: str,
    geometry_type: str = "POLYGON",
    spatial_reference_wkid: int = 4326,
    has_m: str = "DISABLED",
    has_z: str = "DISABLED",
) -> Dict[str, Any]:
    """Creates an empty feature class in a geodatabase or folder.

    Parameters:
        out_path: Destination geodatabase or folder path.
        out_name: Name of the new feature class.
        geometry_type: 'POINT', 'MULTIPOINT', 'POLYLINE', 'POLYGON', 'MULTPATCH'.
        spatial_reference_wkid: WKID code (e.g., 4326 for WGS84, 3857 for Web Mercator, 2100 for GGRS87).
        has_m: 'ENABLED' or 'DISABLED'.
        has_z: 'ENABLED' or 'DISABLED'.
    """
    req = CreateFeatureClassRequest(
        out_path=out_path,
        out_name=out_name,
        geometry_type=geometry_type,
        spatial_reference_wkid=spatial_reference_wkid,
        has_m=has_m,
        has_z=has_z,
    )
    return DataManagementService.create_feature_class(
        out_path=req.out_path,
        out_name=req.out_name,
        geometry_type=req.geometry_type,
        spatial_reference_wkid=req.spatial_reference_wkid,
        has_m=req.has_m,
        has_z=req.has_z,
    )


@arcpy_safe
def list_gdb_contents(gdb_path: str) -> Dict[str, Any]:
    """Inspects a File Geodatabase (.gdb) and catalogs all feature classes, tables,

    feature datasets, and rasters.
    """
    req = ListGDBContentsRequest(gdb_path=gdb_path)
    return DataManagementService.list_gdb_contents(req.gdb_path)


@arcpy_safe
def describe_dataset(dataset_path: str) -> Dict[str, Any]:
    """Returns comprehensive metadata, schema, fields, extent, and geometry info for any dataset.

    Parameters:
        dataset_path: Path to shapefile, GDB feature class, table, or raster.
    """
    req = DescribeDatasetRequest(dataset_path=dataset_path)
    return DataManagementService.describe_dataset(req.dataset_path)


@arcpy_safe
def export_dataset(
    in_data: str,
    out_data: str,
    where_clause: Optional[str] = None,
) -> Dict[str, Any]:
    """Exports or converts datasets between formats (Shapefile, Feature Class, GeoJSON, CSV).

    Parameters:
        in_data: Input feature class or table.
        out_data: Destination path (e.g. .shp, inside .gdb, .geojson).
        where_clause: Optional SQL where clause to filter rows during export.
    """
    req = ExportDatasetRequest(
        in_data=in_data,
        out_data=out_data,
        where_clause=where_clause,
    )
    return DataManagementService.export_dataset(
        in_data=req.in_data,
        out_data=req.out_data,
        where_clause=req.where_clause,
    )


@arcpy_safe
def add_field(
    in_table: str,
    field_name: str,
    field_type: str = "TEXT",
    field_length: int = 255,
    field_alias: Optional[str] = None,
    field_is_nullable: bool = True,
) -> Dict[str, Any]:
    """Adds a new column / field to a feature class or table.

    Parameters:
        in_table: Table or feature class path.
        field_name: Name of the field to add.
        field_type: 'TEXT', 'FLOAT', 'DOUBLE', 'SHORT', 'LONG', 'DATE', 'BLOB'.
        field_length: Character length (for TEXT fields).
        field_alias: Human-readable alias name.
        field_is_nullable: Whether NULL values are permitted.
    """
    req = AddFieldRequest(
        in_table=in_table,
        field_name=field_name,
        field_type=field_type,
        field_length=field_length,
        field_alias=field_alias,
        field_is_nullable=field_is_nullable,
    )
    return DataManagementService.add_field(
        in_table=req.in_table,
        field_name=req.field_name,
        field_type=req.field_type,
        field_length=req.field_length,
        field_alias=req.field_alias,
        field_is_nullable=req.field_is_nullable,
    )


@arcpy_safe
def delete_dataset(target_data: str) -> Dict[str, Any]:
    """Deletes an ArcGIS dataset (feature class, table, or raster) safely.

    Parameters:
        target_data: Path to dataset to delete.
    """
    req = DeleteDatasetRequest(dataset_path=target_data)
    return DataManagementService.delete_dataset(req.dataset_path)
