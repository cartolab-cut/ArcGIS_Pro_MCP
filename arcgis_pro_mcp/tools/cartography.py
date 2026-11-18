"""Cartography, symbology, and labeling tools for ArcGIS Pro MCP Server."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from ..models import (
    ApplySymbologyFromLayerRequest,
    CreateLayerFileRequest,
    SetLayerLabelsRequest,
    SetLayerSymbologyRequest,
)
from ..services.cartography_service import CartographyService
from ..utils import arcpy_safe


@arcpy_safe
def set_layer_symbology(
    project_path: str,
    map_name: str,
    layer_name: str,
    renderer_type: str = "SimpleRenderer",
    symbol_color: Optional[Union[Dict[str, Any], List[int], str]] = None,
    symbol_size: Optional[float] = None,
    outline_color: Optional[Union[Dict[str, Any], List[int], str]] = None,
    outline_width: Optional[float] = None,
    field_name: Optional[str] = None,
    color_ramp_name: Optional[str] = None,
    break_count: Optional[int] = 5,
    classification_method: Optional[str] = "NaturalBreaks",
    save_copy_path: Optional[str] = None,
    export_lyrx: bool = False,
) -> Dict[str, Any]:
    """Applies a symbology renderer (SimpleRenderer, UniqueValueRenderer, GraduatedColorsRenderer) to a layer in an ArcGIS Pro project.

    Parameters:
        project_path: Path to the .aprx project file.
        map_name: Name of the map containing the layer.
        layer_name: Name of the target layer.
        renderer_type: 'SimpleRenderer', 'UniqueValueRenderer', or 'GraduatedColorsRenderer'.
        symbol_color: RGB list [r, g, b] or [r, g, b, a], hex string '#RRGGBB', or dict {'RGB': [r, g, b, a]}.
        symbol_size: Symbol size (for points) or width (for lines).
        outline_color: Outline color for polygon or point symbols.
        outline_width: Outline width in points.
        field_name: Classification field for UniqueValueRenderer or GraduatedColorsRenderer.
        color_ramp_name: Optional name of the color ramp from project styles.
        break_count: Number of classes for GraduatedColorsRenderer (default: 5).
        classification_method: 'NaturalBreaks', 'EqualInterval', 'Quantile', 'GeometricInterval'.
        save_copy_path: Optional path to save a copy of the modified .aprx.
        export_lyrx: Whether to export an updated .lyrx file into the project directory (default: False).
    """
    req = SetLayerSymbologyRequest(
        project_path=project_path,
        map_name=map_name,
        layer_name=layer_name,
        renderer_type=renderer_type,
        symbol_color=symbol_color,
        symbol_size=symbol_size,
        outline_color=outline_color,
        outline_width=outline_width,
        field_name=field_name,
        color_ramp_name=color_ramp_name,
        break_count=break_count,
        classification_method=classification_method,
        save_copy_path=save_copy_path,
        export_lyrx=export_lyrx,
    )
    return CartographyService.set_layer_symbology(
        project_path=req.project_path,
        map_name=req.map_name,
        layer_name=req.layer_name,
        renderer_type=req.renderer_type,
        symbol_color=req.symbol_color,
        symbol_size=req.symbol_size,
        outline_color=req.outline_color,
        outline_width=req.outline_width,
        field_name=req.field_name,
        color_ramp_name=req.color_ramp_name,
        break_count=req.break_count,
        classification_method=req.classification_method,
        save_copy_path=req.save_copy_path,
        export_lyrx=req.export_lyrx,
    )


@arcpy_safe
def set_layer_labels(
    project_path: str,
    map_name: str,
    layer_name: str,
    enable_labels: bool = True,
    expression: Optional[str] = None,
    font_size: Optional[float] = 10.0,
    font_color: Optional[Union[Dict[str, Any], List[int], str]] = None,
    font_family: Optional[str] = "Arial",
    sql_query: Optional[str] = None,
    save_copy_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Configures dynamic labeling, Arcade expressions, and font styling for a layer.

    Parameters:
        project_path: Path to the .aprx project file.
        map_name: Name of the map containing the layer.
        layer_name: Name of the target layer.
        enable_labels: Whether labels should be visible (True/False).
        expression: Arcade label expression (e.g., '$feature.Name' or '\"ID: \" + $feature.ID').
        font_size: Label text size in points.
        font_color: Label color as hex string, RGB list, or dict.
        font_family: Font family name (default: 'Arial').
        sql_query: Optional SQL query to restrict which features are labeled.
        save_copy_path: Optional path to save a copy of the modified project.
    """
    req = SetLayerLabelsRequest(
        project_path=project_path,
        map_name=map_name,
        layer_name=layer_name,
        enable_labels=enable_labels,
        expression=expression,
        font_size=font_size,
        font_color=font_color,
        font_family=font_family,
        sql_query=sql_query,
        save_copy_path=save_copy_path,
    )
    return CartographyService.set_layer_labels(
        project_path=req.project_path,
        map_name=req.map_name,
        layer_name=req.layer_name,
        enable_labels=req.enable_labels,
        expression=req.expression,
        font_size=req.font_size,
        font_color=req.font_color,
        font_family=req.font_family,
        sql_query=req.sql_query,
        save_copy_path=req.save_copy_path,
    )


@arcpy_safe
def apply_symbology_from_layer(
    in_layer: str,
    symbology_layer: str,
    symbology_fields: Optional[str] = None,
    update_symbology: str = "DEFAULT",
) -> Dict[str, Any]:
    """Applies the symbology and rendering properties from another layer or .lyrx file.

    Parameters:
        in_layer: Target layer or feature class to be styled.
        symbology_layer: Source layer or .lyrx file that contains the desired symbology.
        symbology_fields: Field mapping specification (e.g., 'VALUE_FIELD cat cat').
        update_symbology: 'DEFAULT', 'UPDATE', or 'MAINTAIN'.
    """
    req = ApplySymbologyFromLayerRequest(
        in_layer=in_layer,
        symbology_layer=symbology_layer,
        symbology_fields=symbology_fields,
        update_symbology=update_symbology,
    )
    return CartographyService.apply_symbology_from_layer(
        in_layer=req.in_layer,
        symbology_layer=req.symbology_layer,
        symbology_fields=req.symbology_fields,
        update_symbology=req.update_symbology,
    )


@arcpy_safe
def create_layer_file(
    project_path: str,
    map_name: str,
    layer_name: str,
    out_lyrx_path: str,
) -> Dict[str, Any]:
    """Exports a styled layer from an ArcGIS Pro project to a standalone .lyrx file.

    Parameters:
        project_path: Path to the .aprx project file.
        map_name: Name of the map containing the layer.
        layer_name: Name of the layer to export.
        out_lyrx_path: Destination path for the .lyrx file.
    """
    req = CreateLayerFileRequest(
        project_path=project_path,
        map_name=map_name,
        layer_name=layer_name,
        out_lyrx_path=out_lyrx_path,
    )
    return CartographyService.create_layer_file(
        project_path=req.project_path,
        map_name=req.map_name,
        layer_name=req.layer_name,
        out_lyrx_path=req.out_lyrx_path,
    )
