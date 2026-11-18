"""Attribute queries, selections, and analytical statistics tools for ArcGIS Pro MCP Server."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..models import (
    CalculateFieldRequest,
    GetSummaryStatisticsRequest,
    QueryFeaturesRequest,
    SelectFeaturesByAttributeRequest,
    SelectFeaturesByLocationRequest,
)
from ..services.analysis_service import AnalysisService
from ..utils import arcpy_safe


@arcpy_safe
def query_features(
    feature_class: str,
    where_clause: Optional[str] = None,
    fields: Optional[List[str]] = None,
    limit: int = 50,
    offset: int = 0,
    include_geometry_wkt: bool = False,
) -> Dict[str, Any]:
    """Queries features from a feature class or table using an SQL WHERE clause.

    Returns structured rows/records.

    Parameters:
        feature_class: Path to feature class or table.
        where_clause: SQL query string (e.g., "POPULATION > 50000" or "STATUS = 'Active'").
        fields: Specific field names to retrieve. If omitted, all non-geometry fields are fetched.
        limit: Maximum number of rows to return (default: 50, max: 1000).
        offset: Number of initial rows to skip (pagination).
        include_geometry_wkt: Whether to return geometry formatted as Well-Known Text (WKT).
    """
    req = QueryFeaturesRequest(
        feature_class=feature_class,
        where_clause=where_clause,
        fields=fields,
        limit=limit,
        offset=offset,
        include_geometry_wkt=include_geometry_wkt,
    )
    return AnalysisService.query_features(
        feature_class=req.feature_class,
        where_clause=req.where_clause,
        fields=req.fields,
        limit=req.limit,
        offset=req.offset,
        include_geometry_wkt=req.include_geometry_wkt,
    )


@arcpy_safe
def calculate_field(
    in_table: str,
    field: str,
    expression: str,
    expression_type: str = "PYTHON3",
    code_block: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculates or populates values of a field in a feature class or table using Python.

    Parameters:
        in_table: Path to table or feature class.
        field: Name of field to calculate.
        expression: Calculation expression (e.g. '!POPULATION! / !AREA_SQKM!' or 'auto_code(!NAME!)').
        expression_type: Calculation engine (default: 'PYTHON3').
        code_block: Multi-line Python function block if complex logic is used.
    """
    req = CalculateFieldRequest(
        in_table=in_table,
        field=field,
        expression=expression,
        expression_type=expression_type,
        code_block=code_block,
    )
    return AnalysisService.calculate_field(
        in_table=req.in_table,
        field=req.field,
        expression=req.expression,
        expression_type=req.expression_type,
        code_block=req.code_block,
    )


@arcpy_safe
def select_features_by_attribute(
    in_layer: str,
    out_feature_class: str,
    where_clause: str,
) -> Dict[str, Any]:
    """Selects features using an SQL WHERE clause and writes them to a new feature class.

    Parameters:
        in_layer: Input feature class or layer.
        out_feature_class: Destination feature class path.
        where_clause: SQL query string (e.g., "ZONE = 'Residential' AND VAL > 100").
    """
    req = SelectFeaturesByAttributeRequest(
        in_layer=in_layer,
        out_feature_class=out_feature_class,
        where_clause=where_clause,
    )
    return AnalysisService.select_features_by_attribute(
        in_layer=req.in_layer,
        out_feature_class=req.out_feature_class,
        where_clause=req.where_clause,
    )


@arcpy_safe
def select_features_by_location(
    target_layer: str,
    selecting_features: str,
    out_feature_class: str,
    overlap_type: str = "INTERSECT",
    search_distance: Optional[str] = None,
    invert_spatial_relationship: bool = False,
) -> Dict[str, Any]:
    """Selects features based on their spatial relationship with features in another dataset

    and exports the result.

    Parameters:
        target_layer: Features to be selected from.
        selecting_features: Features used to evaluate the spatial relationship.
        out_feature_class: Output path to save selected features.
        overlap_type: 'INTERSECT', 'WITHIN_A_DISTANCE', 'CONTAINS', 'COMPLETELY_CONTAINS',
                      'WITHIN', 'COMPLETELY_WITHIN', 'ARE_IDENTICAL_TO', 'BOUNDARY_TOUCHES',
                      'SHARE_A_LINE_SEGMENT_WITH', 'CROSSED_BY_THE_OUTLINE_OF', 'HAVE_THEIR_CENTER_IN'.
        search_distance: Distance string (e.g. '500 Meters') when using 'WITHIN_A_DISTANCE'.
        invert_spatial_relationship: If True, selects features that DO NOT have the relationship.
    """
    req = SelectFeaturesByLocationRequest(
        target_layer=target_layer,
        selecting_features=selecting_features,
        out_feature_class=out_feature_class,
        overlap_type=overlap_type,
        search_distance=search_distance,
        invert_spatial_relationship=invert_spatial_relationship,
    )
    return AnalysisService.select_features_by_location(
        target_layer=req.target_layer,
        selecting_features=req.selecting_features,
        out_feature_class=req.out_feature_class,
        overlap_type=req.overlap_type,
        search_distance=req.search_distance,
        invert_spatial_relationship=req.invert_spatial_relationship,
    )


@arcpy_safe
def get_summary_statistics(
    in_table: str,
    statistics_fields: List[List[str]],
    case_fields: Optional[List[str]] = None,
    out_table: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculates summary statistics (SUM, MEAN, MIN, MAX, STD, COUNT) for fields in a table.

    Parameters:
        in_table: Table or feature class path.
        statistics_fields: List of [field_name, stat_type] pairs (e.g. [['POPULATION', 'SUM'], ['ELEVATION', 'MEAN']]).
        case_fields: Optional fields to group calculations by (e.g. ['COUNTY_NAME']).
        out_table: Optional output table path. If omitted, uses high-speed in-memory workspace ('memory/temp_stats_tbl').
    """
    req = GetSummaryStatisticsRequest(
        in_table=in_table,
        statistics_fields=statistics_fields,
        case_fields=case_fields,
        out_table=out_table,
    )
    return AnalysisService.get_summary_statistics(
        in_table=req.in_table,
        statistics_fields=req.statistics_fields,
        case_fields=req.case_fields,
        out_table=req.out_table,
    )
