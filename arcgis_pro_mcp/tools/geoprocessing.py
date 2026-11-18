"""Geoprocessing and spatial analysis tools for ArcGIS Pro MCP Server."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..models import (
    BufferAnalysisRequest,
    ClipAnalysisRequest,
    DissolveFeaturesRequest,
    IntersectAnalysisRequest,
    RunGeoprocessingToolRequest,
    SpatialJoinRequest,
)
from ..services.gp_service import GeoprocessingService
from ..utils import arcpy_safe


@arcpy_safe
def run_geoprocessing_tool(
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Dynamically executes any ArcPy geoprocessing tool by name with keyword arguments.

    Example tools: 'Buffer_analysis', 'Clip_analysis', 'SpatialJoin_analysis',
    'Intersect_analysis', 'Dissolve_management', 'CalculateGeometryAttributes_management'.

    Parameters:
        tool_name: Name of tool including toolbox suffix if applicable (e.g. 'Buffer_analysis').
        arguments: Dictionary of parameter names and values.
    """
    req = RunGeoprocessingToolRequest(
        tool_name=tool_name,
        arguments=arguments,
    )
    return GeoprocessingService.run_geoprocessing_tool(
        tool_name=req.tool_name,
        arguments=req.arguments,
    )


@arcpy_safe
def buffer_analysis(
    in_features: str,
    out_feature_class: str,
    buffer_distance_or_field: str,
    line_side: str = "FULL",
    line_end_type: str = "ROUND",
    dissolve_option: str = "NONE",
) -> Dict[str, Any]:
    """Creates buffer polygons around input features to a specified distance.

    Parameters:
        in_features: Path or layer name of features to be buffered.
        out_feature_class: Destination path for buffered features.
        buffer_distance_or_field: Distance with units (e.g., '500 Meters', '2 Kilometers', '100 Feet') or a numeric field name.
        line_side: 'FULL', 'LEFT', 'RIGHT', 'OUTSIDE_ONLY'.
        line_end_type: 'ROUND', 'FLAT'.
        dissolve_option: 'NONE', 'ALL', 'LIST'.
    """
    req = BufferAnalysisRequest(
        in_features=in_features,
        out_feature_class=out_feature_class,
        buffer_distance_or_field=buffer_distance_or_field,
        line_side=line_side,
        line_end_type=line_end_type,
        dissolve_option=dissolve_option,
    )
    return GeoprocessingService.buffer_analysis(
        in_features=req.in_features,
        out_feature_class=req.out_feature_class,
        buffer_distance_or_field=req.buffer_distance_or_field,
        line_side=req.line_side,
        line_end_type=req.line_end_type,
        dissolve_option=req.dissolve_option,
    )


@arcpy_safe
def clip_analysis(
    in_features: str,
    clip_features: str,
    out_feature_class: str,
    cluster_tolerance: Optional[str] = None,
) -> Dict[str, Any]:
    """Clips a feature class using another polygon feature layer boundary.

    Parameters:
        in_features: Features to be clipped.
        clip_features: Features used to clip the input.
        out_feature_class: Path to save clipped output.
        cluster_tolerance: Optional snapping distance with units (e.g. '1 Meter').
    """
    req = ClipAnalysisRequest(
        in_features=in_features,
        clip_features=clip_features,
        out_feature_class=out_feature_class,
        cluster_tolerance=cluster_tolerance,
    )
    return GeoprocessingService.clip_analysis(
        in_features=req.in_features,
        clip_features=req.clip_features,
        out_feature_class=req.out_feature_class,
        cluster_tolerance=req.cluster_tolerance,
    )


@arcpy_safe
def intersect_analysis(
    in_features: List[str],
    out_feature_class: str,
    join_attributes: str = "ALL",
    cluster_tolerance: Optional[str] = None,
    output_type: str = "INPUT",
) -> Dict[str, Any]:
    """Computes a geometric intersection of the input features.

    Parameters:
        in_features: List of paths to input feature classes.
        out_feature_class: Output feature class path.
        join_attributes: 'ALL', 'NO_FID', 'ONLY_FID'.
        cluster_tolerance: Minimum distance between vertices.
        output_type: 'INPUT', 'LINE', 'POINT'.
    """
    req = IntersectAnalysisRequest(
        in_features=in_features,
        out_feature_class=out_feature_class,
        join_attributes=join_attributes,
        cluster_tolerance=cluster_tolerance,
        output_type=output_type,
    )
    return GeoprocessingService.intersect_analysis(
        in_features=req.in_features,
        out_feature_class=req.out_feature_class,
        join_attributes=req.join_attributes,
        cluster_tolerance=req.cluster_tolerance,
        output_type=req.output_type,
    )


@arcpy_safe
def spatial_join(
    target_features: str,
    join_features: str,
    out_feature_class: str,
    join_operation: str = "JOIN_ONE_TO_ONE",
    join_type: str = "KEEP_ALL",
    match_option: str = "INTERSECT",
    search_radius: Optional[str] = None,
) -> Dict[str, Any]:
    """Joins attributes from one feature layer to another based on spatial relationship.

    Parameters:
        target_features: Target feature class receiving attributes.
        join_features: Features providing attributes.
        out_feature_class: Output joined feature class.
        join_operation: 'JOIN_ONE_TO_ONE' or 'JOIN_ONE_TO_MANY'.
        join_type: 'KEEP_ALL' or 'KEEP_COMMON'.
        match_option: 'INTERSECT', 'WITHIN_A_DISTANCE', 'CONTAINS', 'WITHIN', etc.
        search_radius: Distance with units when match_option is 'WITHIN_A_DISTANCE'.
    """
    req = SpatialJoinRequest(
        target_features=target_features,
        join_features=join_features,
        out_feature_class=out_feature_class,
        join_operation=join_operation,
        join_type=join_type,
        match_option=match_option,
        search_radius=search_radius,
    )
    return GeoprocessingService.spatial_join(
        target_features=req.target_features,
        join_features=req.join_features,
        out_feature_class=req.out_feature_class,
        join_operation=req.join_operation,
        join_type=req.join_type,
        match_option=req.match_option,
        search_radius=req.search_radius,
    )


@arcpy_safe
def dissolve_features(
    in_features: str,
    out_feature_class: str,
    dissolve_fields: Optional[List[str]] = None,
    statistics_fields: Optional[List[List[str]]] = None,
    multi_part: bool = True,
) -> Dict[str, Any]:
    """Aggregates features that have the same attribute values.

    Parameters:
        in_features: Input features to dissolve.
        out_feature_class: Output dissolved feature class.
        dissolve_fields: List of field names to group by.
        statistics_fields: List of [field, stat_type] pairs (e.g., [['POPULATION', 'SUM']]).
        multi_part: True to allow multipart polygons/lines.
    """
    req = DissolveFeaturesRequest(
        in_features=in_features,
        out_feature_class=out_feature_class,
        dissolve_fields=dissolve_fields,
        statistics_fields=statistics_fields,
        multi_part=multi_part,
    )
    return GeoprocessingService.dissolve_features(
        in_features=req.in_features,
        out_feature_class=req.out_feature_class,
        dissolve_fields=req.dissolve_fields,
        statistics_fields=req.statistics_fields,
        multi_part=req.multi_part,
    )
