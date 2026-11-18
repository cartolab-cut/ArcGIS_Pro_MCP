"""Pydantic v2 schemas and models for ArcGIS Pro MCP Server.

Provides strict parameter validation, type casting, and schema introspection.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import (
    AspectMethod,
    BasemapName,
    ClassificationMethod,
    DissolveOption,
    ExtensionAction,
    FieldType,
    GeometryType,
    LineEndType,
    LineSide,
    RasterExportFormat,
    SlopeMeasurement,
    SpatialRelationship,
    SymbologyRendererType,
)


class BaseMCPModel(BaseModel):
    """Base Pydantic model with lenient string coercion and documentation support."""
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="allow",
    )


# ---------------------------------------------------------------------------
# Data Management Schemas
# ---------------------------------------------------------------------------

class CreateFileGDBRequest(BaseMCPModel):
    """Parameters for creating a File Geodatabase (.gdb)."""
    out_folder_path: str = Field(description="Folder where the geodatabase will be created.")
    gdb_name: str = Field(description="Name of the geodatabase (with or without .gdb extension).")


class CreateFeatureClassRequest(BaseMCPModel):
    """Parameters for creating a feature class."""
    out_path: str = Field(description="Destination geodatabase or folder path.")
    out_name: str = Field(description="Name of the new feature class.")
    geometry_type: Union[GeometryType, str] = Field(
        default=GeometryType.POLYGON,
        description="Geometry type: POINT, MULTIPOINT, POLYLINE, POLYGON, MULTIPATCH.",
    )
    spatial_reference_wkid: int = Field(
        default=4326,
        description="WKID code (e.g. 4326 for WGS84, 3857 for Web Mercator, 2100 for GGRS87).",
    )
    has_m: str = Field(default="DISABLED", description="'ENABLED' or 'DISABLED'.")
    has_z: str = Field(default="DISABLED", description="'ENABLED' or 'DISABLED'.")

    @field_validator("geometry_type", mode="before")
    @classmethod
    def validate_geometry_type(cls, v: Any) -> str:
        if isinstance(v, GeometryType):
            return v.value
        s = str(v).strip().upper()
        valid = [e.value for e in GeometryType]
        if s not in valid:
            raise ValueError(f"Invalid geometry_type '{v}'. Must be one of: {valid}")
        return s


class AddFieldRequest(BaseMCPModel):
    """Parameters for adding a field/column to a feature class or table."""
    in_table: str = Field(description="Table or feature class path.")
    field_name: str = Field(description="Name of the field to add.")
    field_type: Union[FieldType, str] = Field(
        default=FieldType.TEXT,
        description="Field type: TEXT, FLOAT, DOUBLE, SHORT, LONG, DATE, BLOB.",
    )
    field_length: int = Field(default=255, description="Character length for TEXT fields.")
    field_alias: Optional[str] = Field(default=None, description="Human-readable alias name.")
    field_is_nullable: bool = Field(default=True, description="Whether NULL values are permitted.")


class ExportDatasetRequest(BaseMCPModel):
    """Parameters for converting/exporting datasets."""
    in_data: str = Field(description="Input feature class or table.")
    out_data: str = Field(description="Destination path (e.g. .shp, inside .gdb, .geojson).")
    where_clause: Optional[str] = Field(default=None, description="Optional SQL WHERE clause filter.")


# ---------------------------------------------------------------------------
# Geoprocessing & Spatial Analysis Schemas
# ---------------------------------------------------------------------------

class BufferAnalysisRequest(BaseMCPModel):
    """Parameters for buffer geoprocessing."""
    in_features: str = Field(description="Input features to be buffered.")
    out_feature_class: str = Field(description="Destination path for buffered features.")
    buffer_distance_or_field: str = Field(
        description="Distance with units (e.g., '500 Meters', '2 Kilometers') or numeric field name."
    )
    line_side: Union[LineSide, str] = Field(default=LineSide.FULL, description="'FULL', 'LEFT', 'RIGHT', 'OUTSIDE_ONLY'.")
    line_end_type: Union[LineEndType, str] = Field(default=LineEndType.ROUND, description="'ROUND' or 'FLAT'.")
    dissolve_option: Union[DissolveOption, str] = Field(default=DissolveOption.NONE, description="'NONE', 'ALL', 'LIST'.")


class ClipAnalysisRequest(BaseMCPModel):
    """Parameters for polygon or feature clipping."""
    in_features: str = Field(description="Features to be clipped.")
    clip_features: str = Field(description="Clipping boundary features.")
    out_feature_class: str = Field(description="Destination clipped feature class path.")
    cluster_tolerance: Optional[str] = Field(default=None, description="Tolerance distance with units.")


class IntersectAnalysisRequest(BaseMCPModel):
    """Parameters for geometric intersection."""
    in_features: List[str] = Field(description="List of feature classes to intersect.")
    out_feature_class: str = Field(description="Output intersected feature class.")
    join_attributes: str = Field(default="ALL", description="'ALL', 'NO_FID', 'ONLY_FID'.")
    cluster_tolerance: Optional[str] = Field(default=None, description="Tolerance distance.")
    output_type: str = Field(default="INPUT", description="'INPUT', 'LINE', 'POINT'.")


class SpatialJoinRequest(BaseMCPModel):
    """Parameters for spatial join."""
    target_features: str = Field(description="Target layer features.")
    join_features: str = Field(description="Join layer features.")
    out_feature_class: str = Field(description="Output joined feature class.")
    join_operation: str = Field(default="JOIN_ONE_TO_ONE", description="'JOIN_ONE_TO_ONE' or 'JOIN_ONE_TO_MANY'.")
    join_type: str = Field(default="KEEP_ALL", description="'KEEP_ALL' or 'KEEP_COMMON'.")
    match_option: Union[SpatialRelationship, str] = Field(
        default=SpatialRelationship.INTERSECT,
        description="Spatial match option (e.g. 'INTERSECT', 'WITHIN_A_DISTANCE', 'CONTAINS').",
    )
    search_radius: Optional[str] = Field(default=None, description="Distance with units for distance joins.")


class DissolveFeaturesRequest(BaseMCPModel):
    """Parameters for dissolving features by attribute."""
    in_features: str = Field(description="Input features.")
    out_feature_class: str = Field(description="Output dissolved feature class.")
    dissolve_fields: Optional[List[str]] = Field(default=None, description="Fields to aggregate on.")
    statistics_fields: Optional[List[List[str]]] = Field(default=None, description="Optional statistics aggregations.")
    multi_part: bool = Field(default=True, description="Create multipart features.")


# ---------------------------------------------------------------------------
# Attribute & Analysis Query Schemas
# ---------------------------------------------------------------------------

class QueryFeaturesRequest(BaseMCPModel):
    """Parameters for querying table or feature class rows."""
    feature_class: str = Field(description="Path to feature class or table.")
    where_clause: Optional[str] = Field(default=None, description="SQL WHERE clause.")
    fields: Optional[List[str]] = Field(default=None, description="Fields to return.")
    limit: int = Field(default=50, ge=1, le=1000, description="Max rows to return (1-1000).")
    offset: int = Field(default=0, ge=0, description="Number of rows to skip.")
    include_geometry_wkt: bool = Field(default=False, description="Include geometry as Well-Known Text (WKT).")


class CalculateFieldRequest(BaseMCPModel):
    """Parameters for calculating values in a field."""
    in_table: str = Field(description="Path to table or feature class.")
    field: str = Field(description="Field to update.")
    expression: str = Field(description="Calculation expression.")
    expression_type: str = Field(default="PYTHON3", description="Expression engine.")
    code_block: Optional[str] = Field(default=None, description="Optional Python code block.")


class SelectFeaturesByAttributeRequest(BaseMCPModel):
    """Parameters for selecting features using an attribute query."""
    in_layer: str = Field(description="Input layer or feature class.")
    out_feature_class: str = Field(description="Destination feature class.")
    where_clause: str = Field(description="SQL WHERE clause.")


class SelectFeaturesByLocationRequest(BaseMCPModel):
    """Parameters for selecting features using a spatial relationship."""
    target_layer: str = Field(description="Features to select from.")
    selecting_features: str = Field(description="Selecting features.")
    out_feature_class: str = Field(description="Output feature class.")
    overlap_type: Union[SpatialRelationship, str] = Field(
        default=SpatialRelationship.INTERSECT,
        description="Spatial relationship type.",
    )
    search_distance: Optional[str] = Field(default=None, description="Search distance with units.")
    invert_spatial_relationship: bool = Field(default=False, description="Invert selection result.")


# ---------------------------------------------------------------------------
# Project, Map & Symbology Schemas
# ---------------------------------------------------------------------------

class SetBasemapRequest(BaseMCPModel):
    """Parameters for setting a project map basemap."""
    project_path: str = Field(description="Path to .aprx project file.")
    basemap_name: str = Field(description="Gallery basemap name or custom XYZ provider.")
    map_name: Optional[str] = Field(default=None, description="Map name in project.")
    custom_url: Optional[str] = Field(default=None, description="Optional custom tile URL template.")
    save_copy_path: Optional[str] = Field(default=None, description="Optional path to save copy.")
    export_lyrx: bool = Field(default=False, description="Export companion Active_Basemap.lyrx only when requested.")


class SetSpatialReferenceRequest(BaseMCPModel):
    """Parameters for setting a project map coordinate system."""
    project_path: str = Field(description="Path to .aprx project file.")
    epsg_code: int = Field(description="EPSG / factory code (e.g. 4326, 3857, 2100).")
    map_name: Optional[str] = Field(default=None, description="Map name in project.")
    save_copy_path: Optional[str] = Field(default=None, description="Optional path to save copy.")


class ExportMapRequest(BaseMCPModel):
    """Parameters for exporting a map layout."""
    project_path: str = Field(description="Path to .aprx project file.")
    map_name: str = Field(description="Name of the map.")
    output_image_path: str = Field(description="Destination file path.")
    width: int = Field(default=1920, description="Image width in pixels.")
    height: int = Field(default=1080, description="Image height in pixels.")
    resolution_dpi: int = Field(default=300, description="Resolution DPI.")
    format_type: Union[RasterExportFormat, str] = Field(default=RasterExportFormat.PNG, description="Format (PNG, JPEG, PDF, TIFF).")


class SetLayerSymbologyRequest(BaseMCPModel):
    """Parameters for configuring layer symbology renderers.

    Follows WCAG 2.1 cartographic contrast recommendations (>= 3:1 for graphical symbols,
    >= 4.5:1 for critical labels). For choropleths, colorblind-friendly ramps like 'Viridis',
    'Plasma', or 'Cividis' are recommended.
    """
    project_path: str = Field(description="Path to .aprx project file.")
    map_name: str = Field(description="Name of the map containing the layer.")
    layer_name: str = Field(description="Name of target layer.")
    renderer_type: Union[SymbologyRendererType, str] = Field(
        default=SymbologyRendererType.SIMPLE,
        description="Renderer type: 'SimpleRenderer', 'UniqueValueRenderer', 'GraduatedColorsRenderer'.",
    )
    symbol_color: Optional[Union[Dict[str, Any], List[int], str]] = Field(
        default=None,
        description="Color: RGB list [r, g, b] or [r, g, b, a], hex string '#RRGGBB', or dict {'RGB': [r, g, b, a]}.",
    )
    symbol_size: Optional[float] = Field(default=None, description="Symbol size (points) or line width.")
    outline_color: Optional[Union[Dict[str, Any], List[int], str]] = Field(
        default=None,
        description="Outline color for polygon or point symbols.",
    )
    outline_width: Optional[float] = Field(default=None, description="Outline width.")
    field_name: Optional[str] = Field(
        default=None,
        description="Classification field for UniqueValueRenderer or GraduatedColorsRenderer.",
    )
    color_ramp_name: Optional[str] = Field(
        default=None,
        description="Name of color ramp in project styles (e.g. 'Viridis', 'Plasma', 'Pastel Bar').",
    )
    break_count: Optional[int] = Field(
        default=5,
        ge=2,
        le=32,
        description="Number of classes for GraduatedColorsRenderer (2-32).",
    )
    classification_method: Optional[Union[ClassificationMethod, str]] = Field(
        default=ClassificationMethod.NATURAL_BREAKS,
        description="Method: 'NaturalBreaks', 'EqualInterval', 'Quantile', 'GeometricInterval'.",
    )
    save_copy_path: Optional[str] = Field(default=None, description="Optional path to save copy.")
    export_lyrx: bool = Field(default=False, description="Export updated layer as .lyrx file only when explicitly requested.")


class SetLayerLabelsRequest(BaseMCPModel):
    """Parameters for configuring layer labeling."""
    project_path: str = Field(description="Path to .aprx project file.")
    map_name: str = Field(description="Map name.")
    layer_name: str = Field(description="Layer name.")
    enable_labels: bool = Field(default=True, description="Enable or disable label visibility.")
    expression: Optional[str] = Field(
        default=None,
        description="Arcade label expression (e.g. '$feature.FieldName' or '\"Name: \" + $feature.Name').",
    )
    font_size: Optional[float] = Field(default=10.0, description="Label font size in points.")
    font_color: Optional[Union[Dict[str, Any], List[int], str]] = Field(
        default=None,
        description="Font color: RGB list [r, g, b, a] or hex string.",
    )
    font_family: Optional[str] = Field(default="Arial", description="Font family name.")
    sql_query: Optional[str] = Field(default=None, description="Optional SQL query to filter labeled features.")
    save_copy_path: Optional[str] = Field(default=None, description="Optional path to save copy.")


class ApplySymbologyFromLayerRequest(BaseMCPModel):
    """Parameters for applying symbology from a .lyrx file or reference layer."""
    in_layer: str = Field(description="Target layer path or name.")
    symbology_layer: str = Field(description="Source .lyrx file or reference layer with symbology.")
    symbology_fields: Optional[str] = Field(
        default=None,
        description="Field mapping rule (e.g. 'VALUE_FIELD cat cat').",
    )
    update_symbology: str = Field(default="DEFAULT", description="'DEFAULT', 'UPDATE', or 'MAINTAIN'.")


class CreateLayerFileRequest(BaseMCPModel):
    """Parameters for exporting a layer definition to .lyrx."""
    project_path: str = Field(description="Path to .aprx project file.")
    map_name: str = Field(description="Map name.")
    layer_name: str = Field(description="Layer name.")
    out_lyrx_path: str = Field(description="Destination .lyrx file path.")


# ---------------------------------------------------------------------------
# Additional Tool Schemas
# ---------------------------------------------------------------------------

class DescribeDatasetRequest(BaseMCPModel):
    """Parameters for describing a dataset."""
    dataset_path: str = Field(description="Path to shapefile, GDB feature class, table, or raster.")


class DeleteDatasetRequest(BaseMCPModel):
    """Parameters for deleting a dataset."""
    dataset_path: str = Field(description="Path to feature class, shapefile, table, or raster to delete.")


class ListGDBContentsRequest(BaseMCPModel):
    """Parameters for inspecting File GDB contents."""
    gdb_path: str = Field(description="Path to the File Geodatabase (.gdb).")


class GetSummaryStatisticsRequest(BaseMCPModel):
    """Parameters for calculating summary statistics."""
    in_table: str = Field(description="Input table or feature class path.")
    out_table: Optional[str] = Field(
        default=None,
        description="Optional output summary table path (uses high-speed 'memory/' workspace if omitted).",
    )
    statistics_fields: List[List[str]] = Field(
        description="Statistics fields list (e.g. [['POPULATION', 'SUM'], ['AREA', 'MEAN']])."
    )
    case_fields: Optional[List[str]] = Field(default=None, description="Optional group-by field names.")


class InspectProjectRequest(BaseMCPModel):
    """Parameters for inspecting an ArcGIS Pro project."""
    project_path: str = Field(description="Path to .aprx project file.")


class ListMapLayersRequest(BaseMCPModel):
    """Parameters for listing layers in a project map."""
    project_path: str = Field(description="Path to .aprx project file.")
    map_name: Optional[str] = Field(default=None, description="Map name in project.")


class GetLayerPropertiesRequest(BaseMCPModel):
    """Parameters for inspecting layer properties."""
    project_path: str = Field(description="Path to .aprx project file.")
    map_name: str = Field(description="Map name.")
    layer_name: str = Field(description="Layer name.")


class AddLayerToMapRequest(BaseMCPModel):
    """Parameters for adding a layer to a map."""
    project_path: str = Field(description="Path to .aprx project file.")
    map_name: str = Field(description="Map name.")
    data_path: str = Field(description="Path to feature class, shapefile, or raster.")
    save_copy_path: Optional[str] = Field(default=None, description="Optional path to save modified .aprx.")


class DescribeRasterRequest(BaseMCPModel):
    """Parameters for describing a raster dataset."""
    raster_path: str = Field(description="Path to raster dataset or image file.")


class CreateHillshadeRequest(BaseMCPModel):
    """Parameters for creating a shaded relief raster."""
    in_dem: str = Field(description="Input elevation raster DEM.")
    out_raster: str = Field(description="Destination path for hillshade raster.")
    azimuth: float = Field(default=315.0, ge=0.0, le=360.0, description="Light source azimuth angle (0-360).")
    altitude: float = Field(default=45.0, ge=0.0, le=90.0, description="Light source altitude angle (0-90).")
    z_factor: float = Field(default=1.0, gt=0.0, description="Vertical exaggeration factor.")


class CalculateSlopeRequest(BaseMCPModel):
    """Parameters for slope analysis."""
    in_dem: str = Field(description="Input elevation raster DEM.")
    out_raster: str = Field(description="Output slope raster path.")
    output_measurement: Union[SlopeMeasurement, str] = Field(
        default=SlopeMeasurement.DEGREE,
        description="'DEGREE' or 'PERCENT_RISE'.",
    )
    z_factor: float = Field(default=1.0, gt=0.0, description="Vertical exaggeration factor.")


class CalculateAspectRequest(BaseMCPModel):
    """Parameters for aspect analysis."""
    in_dem: str = Field(description="Input elevation raster DEM.")
    out_raster: str = Field(description="Output aspect raster path.")
    method: Union[AspectMethod, str] = Field(default=AspectMethod.PLANAR, description="'PLANAR' or 'GEODESIC'.")


class CreateContoursRequest(BaseMCPModel):
    """Parameters for contour line generation."""
    in_dem: str = Field(description="Input elevation raster DEM.")
    out_feature_class: str = Field(description="Output contour feature class path.")
    interval: float = Field(gt=0.0, description="Contour elevation interval (e.g. 10.0, 50.0).")
    base_contour: float = Field(default=0.0, description="Base contour elevation (default: 0.0).")
    z_factor: float = Field(default=1.0, gt=0.0, description="Vertical exaggeration factor.")


class ExtractRasterByMaskRequest(BaseMCPModel):
    """Parameters for raster mask extraction."""
    in_raster: str = Field(description="Input raster to clip.")
    in_mask_data: str = Field(description="Mask feature class or raster boundary.")
    out_raster: str = Field(description="Destination path for masked raster.")


class ManageExtensionRequest(BaseMCPModel):
    """Parameters for checking extension licenses."""
    extension_name: str = Field(description="Extension name (e.g. 'Spatial', '3D', 'Network').")
    action: Union[ExtensionAction, str] = Field(default=ExtensionAction.STATUS, description="'status', 'check_out', 'check_in'.")


class SetArcGISEnvironmentRequest(BaseMCPModel):
    """Parameters for setting ArcPy environment variables."""
    workspace: Optional[str] = Field(default=None, description="Current workspace path.")
    scratch_workspace: Optional[str] = Field(default=None, description="Scratch workspace path.")
    overwrite_output: Optional[bool] = Field(default=None, description="Allow overwriting existing outputs.")
    extent: Optional[str] = Field(default=None, description="Bounding coordinate extent.")
    output_coordinate_system: Optional[Union[int, str]] = Field(default=None, description="Output coordinate system EPSG.")


class ExecuteArcPyCodeRequest(BaseMCPModel):
    """Parameters for executing dynamic ArcPy Python code."""
    code: str = Field(description="Python script string to execute.")
    return_variables: Optional[List[str]] = Field(default=None, description="Names of variables to capture and return.")


class RunGeoprocessingToolRequest(BaseMCPModel):
    """Parameters for running any ArcPy geoprocessing tool."""
    tool_name: str = Field(description="Geoprocessing tool name (e.g. 'Buffer_analysis').")
    arguments: Optional[Dict[str, Any]] = Field(default=None, description="Keyword arguments for the tool.")
