"""Cartography, symbology, and labeling service for ArcGIS Pro using arcpy.mp."""

from __future__ import annotations
import gc
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union
import arcpy

from ..utils import (
    capture_arcpy_messages,
    is_wcag_accessible,
    sanitize_path,
    stage_ai_live_action,
)


def parse_color_spec(color_val: Any) -> Optional[Dict[str, List[int]]]:
    """Parses hex strings, RGB lists, or color dicts into ArcPy CIM color dictionaries.

    Examples:
        '#FF0000' -> {'RGB': [255, 0, 0, 100]}
        [0, 128, 255] -> {'RGB': [0, 128, 255, 100]}
        [0, 128, 255, 80] -> {'RGB': [0, 128, 255, 80]}
        {'RGB': [255, 0, 0, 100]} -> {'RGB': [255, 0, 0, 100]}
    """
    if not color_val:
        return None

    if isinstance(color_val, dict) and "RGB" in color_val:
        return color_val

    if isinstance(color_val, (list, tuple)):
        vals = [int(v) for v in color_val]
        if len(vals) == 3:
            return {"RGB": [vals[0], vals[1], vals[2], 100]}
        elif len(vals) >= 4:
            return {"RGB": [vals[0], vals[1], vals[2], vals[3]]}

    if isinstance(color_val, str):
        c = color_val.strip().lstrip("#")
        if len(c) == 6:
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
            return {"RGB": [r, g, b, 100]}
        elif len(c) == 8:
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
            a = int(c[6:8], 16)
            return {"RGB": [r, g, b, a]}

    return None


class CartographyService:
    """Service layer encapsulating layer symbology, renderers, labeling, and layer file creation."""

    @staticmethod
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
        """Configures symbology renderer (SimpleRenderer, UniqueValueRenderer, GraduatedColorsRenderer)."""
        clean_proj = sanitize_path(project_path)
        if not os.path.isfile(clean_proj):
            return {"success": False, "error": f"Project file not found at: {clean_proj}"}

        aprx = arcpy.mp.ArcGISProject(clean_proj)
        try:
            target_map = None
            for m in aprx.listMaps():
                if m.name.lower() == map_name.lower():
                    target_map = m
                    break
            if not target_map:
                return {"success": False, "error": f"Map '{map_name}' not found."}

            target_layer = None
            for lyr in target_map.listLayers():
                if lyr.name.lower() == layer_name.lower():
                    target_layer = lyr
                    break
            if not target_layer:
                return {"success": False, "error": f"Layer '{layer_name}' not found in map '{map_name}'."}

            if not hasattr(target_layer, "symbology"):
                return {"success": False, "error": f"Layer '{layer_name}' does not support symbology."}

            sym = target_layer.symbology
            clean_renderer = str(renderer_type).strip()

            available_fields: List[str] = []
            try:
                desc = arcpy.da.Describe(target_layer)
                available_fields = [f.name for f in desc.get("fields", [])]
            except Exception:
                pass

            if field_name and available_fields and field_name not in available_fields:
                return {
                    "success": False,
                    "error": f"Field '{field_name}' not found on layer '{target_layer.name}'. Available fields: {available_fields}",
                }

            # 1. SimpleRenderer
            if clean_renderer.lower() in ("simplerenderer", "simple"):
                if sym.renderer.type != "SimpleRenderer":
                    sym.updateRenderer("SimpleRenderer")

                parsed_color = parse_color_spec(symbol_color)
                if parsed_color and hasattr(sym.renderer.symbol, "color"):
                    sym.renderer.symbol.color = parsed_color

                if symbol_size is not None:
                    if hasattr(sym.renderer.symbol, "size"):
                        sym.renderer.symbol.size = float(symbol_size)
                    elif hasattr(sym.renderer.symbol, "width"):
                        sym.renderer.symbol.width = float(symbol_size)

                parsed_outline = parse_color_spec(outline_color)
                if parsed_outline and hasattr(sym.renderer.symbol, "outlineColor"):
                    sym.renderer.symbol.outlineColor = parsed_outline

                if outline_width is not None and hasattr(sym.renderer.symbol, "outlineWidth"):
                    sym.renderer.symbol.outlineWidth = float(outline_width)

                target_layer.symbology = sym

            # 2. UniqueValueRenderer
            elif clean_renderer.lower() in ("uniquevaluerenderer", "unique_value", "uniquevalue"):
                sym.updateRenderer("UniqueValueRenderer")
                if field_name:
                    sym.renderer.fields = [field_name]

                if color_ramp_name:
                    ramps = aprx.listColorRamps(color_ramp_name)
                    if ramps:
                        sym.renderer.colorRamp = ramps[0]
                else:
                    all_ramps = aprx.listColorRamps()
                    if all_ramps:
                        sym.renderer.colorRamp = all_ramps[0]

                target_layer.symbology = sym

            # 3. GraduatedColorsRenderer
            elif clean_renderer.lower() in ("graduatedcolorsrenderer", "graduated_colors", "graduatedcolors"):
                if break_count is not None and int(break_count) < 2:
                    return {
                        "success": False,
                        "error": f"GraduatedColorsRenderer requires break_count >= 2, got {break_count}.",
                    }

                sym.updateRenderer("GraduatedColorsRenderer")
                if field_name:
                    sym.renderer.classificationField = field_name
                if break_count:
                    sym.renderer.breakCount = int(break_count)
                if classification_method and hasattr(sym.renderer, "classificationMethod"):
                    try:
                        sym.renderer.classificationMethod = str(classification_method)
                    except Exception:
                        pass

                if color_ramp_name:
                    ramps = aprx.listColorRamps(color_ramp_name)
                    if ramps:
                        sym.renderer.colorRamp = ramps[0]
                else:
                    all_ramps = aprx.listColorRamps()
                    if all_ramps:
                        sym.renderer.colorRamp = all_ramps[0]

                target_layer.symbology = sym

            else:
                return {
                    "success": False,
                    "error": f"Unsupported renderer type '{renderer_type}'. Supported: 'SimpleRenderer', 'UniqueValueRenderer', 'GraduatedColorsRenderer'.",
                }

            # Evaluate WCAG accessibility if color is provided
            accessibility_info = None
            if symbol_color:
                accessibility_info = {
                    "against_white_bg": is_wcag_accessible(symbol_color, "#FFFFFF", min_ratio=3.0),
                    "against_dark_bg": is_wcag_accessible(symbol_color, "#000000", min_ratio=3.0),
                }

            project_dir = os.path.dirname(os.path.abspath(clean_proj))
            lyrx_exported = None
            if export_lyrx:
                sanitized_name = "".join(c for c in target_layer.name if c.isalnum() or c in ("_", "-"))
                lyrx_exported = os.path.join(project_dir, f"{sanitized_name}.lyrx")
                try:
                    target_layer.saveACopy(lyrx_exported)
                except Exception:
                    lyrx_exported = None

            saved_path = None
            if save_copy_path:
                clean_save = sanitize_path(save_copy_path)
                aprx.saveACopy(clean_save)
                saved_path = clean_save
            else:
                try:
                    aprx.save()
                    saved_path = clean_proj
                except OSError:
                    code_lines = [
                        f"m = [m for m in aprx.listMaps() if m.name.lower() == {repr(target_map.name.lower())}][0]",
                        f"lyr = [l for l in m.listLayers() if l.name.lower() == {repr(target_layer.name.lower())}][0]",
                        "sym = lyr.symbology",
                    ]
                    if clean_renderer.lower() in ("simplerenderer", "simple"):
                        code_lines.append("if sym.renderer.type != 'SimpleRenderer': sym.updateRenderer('SimpleRenderer')")
                        if parsed_color:
                            code_lines.append(f"if hasattr(sym.renderer.symbol, 'color'): sym.renderer.symbol.color = {parsed_color}")
                        if symbol_size is not None:
                            code_lines.append(f"if hasattr(sym.renderer.symbol, 'size'): sym.renderer.symbol.size = {float(symbol_size)}")
                            code_lines.append(f"elif hasattr(sym.renderer.symbol, 'width'): sym.renderer.symbol.width = {float(symbol_size)}")
                        if parsed_outline:
                            code_lines.append(f"if hasattr(sym.renderer.symbol, 'outlineColor'): sym.renderer.symbol.outlineColor = {parsed_outline}")
                        if outline_width is not None:
                            code_lines.append(f"if hasattr(sym.renderer.symbol, 'outlineWidth'): sym.renderer.symbol.outlineWidth = {float(outline_width)}")
                    elif clean_renderer.lower() in ("uniquevaluerenderer", "unique_value", "uniquevalue"):
                        code_lines.append("sym.updateRenderer('UniqueValueRenderer')")
                        if field_name:
                            code_lines.append(f"sym.renderer.fields = [{repr(field_name)}]")
                        if color_ramp_name:
                            code_lines.append(f"ramps = aprx.listColorRamps({repr(color_ramp_name)})")
                            code_lines.append("if ramps: sym.renderer.colorRamp = ramps[0]")
                        else:
                            code_lines.append("all_ramps = aprx.listColorRamps()")
                            code_lines.append("if all_ramps: sym.renderer.colorRamp = all_ramps[0]")
                    elif clean_renderer.lower() in ("graduatedcolorsrenderer", "graduated_colors", "graduatedcolors"):
                        code_lines.append("sym.updateRenderer('GraduatedColorsRenderer')")
                        if field_name:
                            code_lines.append(f"sym.renderer.classificationField = {repr(field_name)}")
                        if break_count:
                            code_lines.append(f"sym.renderer.breakCount = {int(break_count)}")
                        if classification_method:
                            code_lines.append(f"if hasattr(sym.renderer, 'classificationMethod'): sym.renderer.classificationMethod = {repr(str(classification_method))}")
                        if color_ramp_name:
                            code_lines.append(f"ramps = aprx.listColorRamps({repr(color_ramp_name)})")
                            code_lines.append("if ramps: sym.renderer.colorRamp = ramps[0]")
                        else:
                            code_lines.append("all_ramps = aprx.listColorRamps()")
                            code_lines.append("if all_ramps: sym.renderer.colorRamp = all_ramps[0]")
                    code_lines.append("lyr.symbology = sym")

                    stage_file = stage_ai_live_action(clean_proj, code_lines)
                    return {
                        "success": False,
                        "error": (
                            f"ArcGIS Pro has '{clean_proj}' open and locked. Staged action to 'ai_live_action.py'. "
                            f"Run 'Run AI Live Task' in ArcGIS Pro to apply changes live without file conflicts."
                        ),
                        "staged_file": stage_file,
                        "layer_name": target_layer.name,
                        "map_name": target_map.name,
                        "renderer_type": clean_renderer,
                        "accessibility": accessibility_info,
                    }

            ret = {
                "success": True,
                "layer_name": target_layer.name,
                "map_name": target_map.name,
                "renderer_type": clean_renderer,
                "classification_field": field_name,
                "saved_project": saved_path,
                "lyrx_exported": lyrx_exported,
                "accessibility": accessibility_info,
            }
            return ret
        finally:
            sym = None
            target_layer = None
            target_map = None
            m = None
            lyr = None
            aprx = None
            gc.collect()

    @staticmethod
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
        """Configures layer label visibility, Arcade expression, and font properties."""
        clean_proj = sanitize_path(project_path)
        if not os.path.isfile(clean_proj):
            return {"success": False, "error": f"Project file not found at: {clean_proj}"}

        aprx = arcpy.mp.ArcGISProject(clean_proj)
        try:
            target_map = None
            for m in aprx.listMaps():
                if m.name.lower() == map_name.lower():
                    target_map = m
                    break
            if not target_map:
                return {"success": False, "error": f"Map '{map_name}' not found."}

            target_layer = None
            for lyr in target_map.listLayers():
                if lyr.name.lower() == layer_name.lower():
                    target_layer = lyr
                    break
            if not target_layer:
                return {"success": False, "error": f"Layer '{layer_name}' not found in map '{map_name}'."}

            if not target_layer.supports("SHOWLABELS"):
                return {"success": False, "error": f"Layer '{layer_name}' does not support labeling."}

            target_layer.showLabels = bool(enable_labels)

            if enable_labels:
                label_classes = target_layer.listLabelClasses()
                if not label_classes and hasattr(target_layer, "createLabelClass"):
                    lc = target_layer.createLabelClass("Class 1", expression or "$feature.OBJECTID")
                    label_classes = [lc]

                for lc in label_classes:
                    if expression:
                        lc.expression = expression
                    if sql_query is not None:
                        lc.SQLQuery = sql_query

                    if font_size or font_color or font_family:
                        try:
                            cim = lc.getDefinition("V3")
                            if font_size:
                                cim.textSymbol.symbol.height = float(font_size)
                            if font_family:
                                cim.textSymbol.symbol.fontFamilyName = str(font_family)
                            parsed_col = parse_color_spec(font_color)
                            if parsed_col:
                                rgb_vals = parsed_col.get("RGB")
                                if rgb_vals and hasattr(cim.textSymbol.symbol, "symbol") and hasattr(cim.textSymbol.symbol.symbol, "symbolLayers"):
                                    for sl in cim.textSymbol.symbol.symbol.symbolLayers:
                                        if hasattr(sl, "color") and hasattr(sl.color, "values"):
                                            sl.color.values = rgb_vals
                            lc.setDefinition(cim)
                        except Exception:
                            pass

            # Evaluate WCAG accessibility if font color is provided
            accessibility_info = None
            if font_color:
                accessibility_info = {
                    "against_white_bg": is_wcag_accessible(font_color, "#FFFFFF", min_ratio=4.5),
                    "against_dark_bg": is_wcag_accessible(font_color, "#000000", min_ratio=4.5),
                }

            project_dir = os.path.dirname(os.path.abspath(clean_proj))
            saved_path = None
            if save_copy_path:
                clean_save = sanitize_path(save_copy_path)
                aprx.saveACopy(clean_save)
                saved_path = clean_save
            else:
                try:
                    aprx.save()
                    saved_path = clean_proj
                except OSError:
                    code_lines = [
                        f"m = [m for m in aprx.listMaps() if m.name.lower() == {repr(target_map.name.lower())}][0]",
                        f"lyr = [l for l in m.listLayers() if l.name.lower() == {repr(target_layer.name.lower())}][0]",
                        "if lyr.supports('SHOWLABELS'):",
                        f"    lyr.showLabels = {bool(enable_labels)}",
                    ]
                    if enable_labels:
                        code_lines.extend([
                            "    label_classes = lyr.listLabelClasses()",
                            "    if not label_classes and hasattr(lyr, 'createLabelClass'):",
                            f"        label_classes = [lyr.createLabelClass('Class 1', {repr(expression or '$feature.OBJECTID')})]",
                            "    for lc in label_classes:",
                        ])
                        if expression:
                            code_lines.append(f"        lc.expression = {repr(expression)}")
                        if sql_query is not None:
                            code_lines.append(f"        lc.SQLQuery = {repr(sql_query)}")
                        if font_size or font_color or font_family:
                            code_lines.extend([
                                "        try:",
                                "            cim = lc.getDefinition('V3')",
                            ])
                            if font_size:
                                code_lines.append(f"            cim.textSymbol.symbol.height = {float(font_size)}")
                            if font_family:
                                code_lines.append(f"            cim.textSymbol.symbol.fontFamilyName = {repr(str(font_family))}")
                            parsed_col = parse_color_spec(font_color)
                            if parsed_col:
                                rgb_vals = parsed_col.get("RGB")
                                if rgb_vals:
                                    code_lines.extend([
                                        "            if hasattr(cim.textSymbol.symbol, 'symbol') and hasattr(cim.textSymbol.symbol.symbol, 'symbolLayers'):",
                                        "                for sl in cim.textSymbol.symbol.symbolLayers:",
                                        f"                    if hasattr(sl, 'color') and hasattr(sl.color, 'values'): sl.color.values = {rgb_vals}",
                                    ])
                            code_lines.extend([
                                "            lc.setDefinition(cim)",
                                "        except Exception:",
                                "            pass",
                            ])
                    stage_file = stage_ai_live_action(clean_proj, code_lines)
                    return {
                        "success": False,
                        "error": (
                            f"ArcGIS Pro has '{clean_proj}' open and locked. Staged action to 'ai_live_action.py'. "
                            f"Run 'Run AI Live Task' in ArcGIS Pro to apply changes live without file conflicts."
                        ),
                        "staged_file": stage_file,
                        "layer_name": target_layer.name,
                        "map_name": target_map.name,
                        "labels_enabled": bool(enable_labels),
                        "accessibility": accessibility_info,
                    }

            return {
                "success": True,
                "layer_name": target_layer.name,
                "labels_enabled": bool(enable_labels),
                "expression": expression,
                "font_size": font_size,
                "font_family": font_family,
                "saved_project": saved_path,
                "accessibility": accessibility_info,
            }
        finally:
            target_layer = None
            target_map = None
            m = None
            lyr = None
            aprx = None
            gc.collect()

    @staticmethod
    def apply_symbology_from_layer(
        in_layer: str,
        symbology_layer: str,
        symbology_fields: Optional[str] = None,
        update_symbology: str = "DEFAULT",
    ) -> Dict[str, Any]:
        """Applies symbology definition from a .lyrx file or existing layer."""
        clean_in = sanitize_path(in_layer)
        clean_sym = sanitize_path(symbology_layer)

        if not os.path.exists(clean_sym) and not arcpy.Exists(clean_sym):
            return {"success": False, "error": f"Symbology source not found at: {clean_sym}"}

        arcpy.management.ApplySymbologyFromLayer(
            in_layer=clean_in,
            in_symbology_layer=clean_sym,
            symbology_fields=symbology_fields or "#",
            update_symbology=update_symbology,
        )

        return {
            "success": True,
            "message": f"Successfully applied symbology from {clean_sym} to {clean_in}",
            "target_layer": clean_in,
            "symbology_source": clean_sym,
            "geoprocessing_messages": capture_arcpy_messages(),
        }

    @staticmethod
    def create_layer_file(
        project_path: str,
        map_name: str,
        layer_name: str,
        out_lyrx_path: str,
    ) -> Dict[str, Any]:
        """Exports a layer from an ArcGIS Pro project to a standalone .lyrx file."""
        clean_proj = sanitize_path(project_path)
        clean_out = sanitize_path(out_lyrx_path)
        os.makedirs(os.path.dirname(os.path.abspath(clean_out)), exist_ok=True)

        aprx = arcpy.mp.ArcGISProject(clean_proj)
        try:
            target_map = None
            for m in aprx.listMaps():
                if m.name.lower() == map_name.lower():
                    target_map = m
                    break
            if not target_map:
                return {"success": False, "error": f"Map '{map_name}' not found."}

            target_layer = None
            for lyr in target_map.listLayers():
                if lyr.name.lower() == layer_name.lower():
                    target_layer = lyr
                    break
            if not target_layer:
                return {"success": False, "error": f"Layer '{layer_name}' not found."}

            target_layer.saveACopy(clean_out)
            return {
                "success": True,
                "message": f"Layer '{layer_name}' saved to layer file at {clean_out}",
                "layer_name": layer_name,
                "out_lyrx_path": clean_out,
            }
        finally:
            target_layer = None
            target_map = None
            m = None
            lyr = None
            aprx = None
            gc.collect()
