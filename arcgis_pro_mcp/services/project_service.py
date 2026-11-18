"""ArcGIS Pro Project (.aprx) and Map management service using arcpy.mp."""

from __future__ import annotations
import gc
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import arcpy

from ..utils import (
    format_extent,
    format_spatial_reference,
    sanitize_path,
    stage_ai_live_action,
)

BUILTIN_BASEMAPS: Dict[str, str] = {
    "topographic": "Topographic",
    "topo": "Topographic",
    "imagery": "Imagery",
    "satellite": "Imagery",
    "hybrid": "Imagery Hybrid",
    "imagery hybrid": "Imagery Hybrid",
    "streets": "Streets",
    "navigation": "Navigation",
    "light gray canvas": "Light Gray Canvas",
    "light gray": "Light Gray Canvas",
    "dark gray canvas": "Dark Gray Canvas",
    "dark gray": "Dark Gray Canvas",
    "oceans": "Oceans",
    "terrain with labels": "Terrain with Labels",
    "terrain": "Terrain with Labels",
    "streets (night)": "Streets (Night)",
    "streets night": "Streets (Night)",
}

KNOWN_CUSTOM_BASEMAPS: Dict[str, str] = {
    "google satellite": "https://mt1.google.com/vt/lyrs=s&x={col}&y={row}&z={level}",
    "google hybrid": "https://mt1.google.com/vt/lyrs=y&x={col}&y={row}&z={level}",
    "google roads": "https://mt1.google.com/vt/lyrs=m&x={col}&y={row}&z={level}",
    "google terrain": "https://mt1.google.com/vt/lyrs=p&x={col}&y={row}&z={level}",
    "openstreetmap": "https://tile.openstreetmap.org/{level}/{col}/{row}.png",
    "osm": "https://tile.openstreetmap.org/{level}/{col}/{row}.png",
    "cartodb dark": "https://a.basemaps.cartocdn.com/dark_all/{level}/{col}/{row}.png",
    "cartodb light": "https://a.basemaps.cartocdn.com/light_all/{level}/{col}/{row}.png",
}


class ProjectService:
    """Service layer encapsulating ArcGIS Pro project (.aprx) and map operations."""

    @staticmethod
    def inspect_project(project_path: str) -> Dict[str, Any]:
        """Inspects an ArcGIS Pro project (.aprx) file and returns its maps, layouts, and databases."""
        clean_path = sanitize_path(project_path)
        if not os.path.isfile(clean_path):
            return {"success": False, "error": f"Project file not found at: {clean_path}"}

        aprx = arcpy.mp.ArcGISProject(clean_path)
        try:
            maps_info = []
            for m in aprx.listMaps():
                maps_info.append({
                    "name": m.name,
                    "map_type": getattr(m, "mapType", "Unknown"),
                    "layer_count": len(m.listLayers()),
                    "table_count": len(m.listTables()),
                    "spatial_reference": format_spatial_reference(m.spatialReference),
                })

            layouts_info = []
            for l in aprx.listLayouts():
                layouts_info.append({
                    "name": l.name,
                    "page_width": getattr(l, "pageWidth", 0),
                    "page_height": getattr(l, "pageHeight", 0),
                    "page_units": getattr(l, "pageUnits", "Unknown"),
                })

            return {
                "success": True,
                "project_path": clean_path,
                "default_geodatabase": aprx.defaultGeodatabase,
                "default_toolbox": aprx.defaultToolbox,
                "home_folder": aprx.homeFolder,
                "maps": maps_info,
                "layouts": layouts_info,
            }
        finally:
            target_map = None
            m = None
            sr = None
            aprx = None
            gc.collect()

    @staticmethod
    def list_map_layers(
        project_path: str,
        map_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Lists all layers and tables within a project's map."""
        clean_path = sanitize_path(project_path)
        if not os.path.isfile(clean_path):
            return {"success": False, "error": f"Project file not found at: {clean_path}"}

        aprx = arcpy.mp.ArcGISProject(clean_path)
        try:
            maps = aprx.listMaps()
            if not maps:
                return {"success": False, "error": "No maps found in project."}

            target_map = None
            if map_name:
                for m in maps:
                    if m.name.lower() == map_name.lower():
                        target_map = m
                        break
                if not target_map:
                    available = [m.name for m in maps]
                    return {"success": False, "error": f"Map '{map_name}' not found. Available maps: {available}"}
            else:
                target_map = maps[0]

            layers_data = []
            for lyr in target_map.listLayers():
                info = {
                    "name": lyr.name,
                    "long_name": getattr(lyr, "longName", lyr.name),
                    "visible": bool(lyr.visible),
                    "is_feature_layer": bool(lyr.isFeatureLayer),
                    "is_raster_layer": bool(lyr.isRasterLayer),
                    "is_group_layer": bool(lyr.isGroupLayer),
                }
                if lyr.isFeatureLayer or lyr.isRasterLayer:
                    try:
                        info["data_source"] = lyr.dataSource
                    except Exception:
                        info["data_source"] = "Unavailable"
                if lyr.isFeatureLayer:
                    try:
                        info["definition_query"] = lyr.definitionQuery
                    except Exception:
                        pass
                layers_data.append(info)

            tables_data = []
            for tbl in target_map.listTables():
                tables_data.append({
                    "name": tbl.name,
                    "data_source": getattr(tbl, "dataSource", "Unavailable"),
                })

            return {
                "success": True,
                "project_path": clean_path,
                "map_name": target_map.name,
                "layers": layers_data,
                "tables": tables_data,
            }
        finally:
            target_map = None
            m = None
            sr = None
            aprx = None
            gc.collect()

    @staticmethod
    def get_layer_properties(
        project_path: str,
        map_name: str,
        layer_name: str,
    ) -> Dict[str, Any]:
        """Retrieves detailed properties, fields schema, extent, and feature count."""
        clean_path = sanitize_path(project_path)
        aprx = arcpy.mp.ArcGISProject(clean_path)
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

            desc_info: Dict[str, Any] = {
                "name": target_layer.name,
                "is_feature_layer": target_layer.isFeatureLayer,
                "is_raster_layer": target_layer.isRasterLayer,
                "visible": target_layer.visible,
            }

            if target_layer.isFeatureLayer:
                try:
                    desc = arcpy.da.Describe(target_layer)
                    fields = []
                    for f in desc.get("fields", []):
                        fields.append({
                            "name": f.name,
                            "type": f.type,
                            "length": f.length,
                            "alias": f.aliasName,
                            "editable": f.editable,
                        })

                    feature_count = int(arcpy.management.GetCount(target_layer)[0])

                    desc_info.update({
                        "data_source": getattr(target_layer, "dataSource", ""),
                        "definition_query": getattr(target_layer, "definitionQuery", ""),
                        "shape_type": desc.get("shapeType"),
                        "feature_count": feature_count,
                        "extent": format_extent(desc.get("extent")),
                        "spatial_reference": format_spatial_reference(desc.get("spatialReference")),
                        "fields": fields,
                    })
                except Exception as e:
                    desc_info["describe_error"] = str(e)

            return {"success": True, "layer_properties": desc_info}
        finally:
            target_map = None
            m = None
            sr = None
            aprx = None
            gc.collect()

    @staticmethod
    def export_map(
        project_path: str,
        map_name: str,
        output_image_path: str,
        width: int = 1920,
        height: int = 1080,
        resolution_dpi: int = 300,
        format_type: str = "PNG",
    ) -> Dict[str, Any]:
        """Exports a project map layout to an image or document."""
        clean_proj = sanitize_path(project_path)
        clean_out = sanitize_path(output_image_path)
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

            exported = False
            for l in aprx.listLayouts():
                for mf in l.listElements("MAPFRAME_ELEMENT"):
                    if mf.map and mf.map.name.lower() == target_map.name.lower():
                        fmt = str(format_type).upper()
                        if fmt == "PNG":
                            l.exportToPNG(clean_out, resolution=resolution_dpi)
                        elif fmt in ("JPEG", "JPG"):
                            l.exportToJPEG(clean_out, resolution=resolution_dpi)
                        elif fmt == "PDF":
                            l.exportToPDF(clean_out, resolution=resolution_dpi)
                        elif fmt == "TIFF":
                            l.exportToTIFF(clean_out, resolution=resolution_dpi)
                        else:
                            l.exportToPNG(clean_out, resolution=resolution_dpi)
                        exported = True
                        return {
                            "success": True,
                            "message": f"Exported map layout frame to {clean_out}",
                            "output_path": clean_out,
                            "layout_used": l.name,
                        }

            if not exported:
                return {
                    "success": False,
                    "error": f"No layout containing a MapFrame for map '{map_name}' was found. In ArcGIS Pro, map exports are rendered via Layout MapFrames.",
                    "available_layouts": [l.name for l in aprx.listLayouts()],
                }
        finally:
            target_map = None
            m = None
            sr = None
            aprx = None
            gc.collect()

    @staticmethod
    def add_layer_to_map(
        project_path: str,
        map_name: str,
        data_path: str,
        save_copy_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Adds a spatial dataset into a project map."""
        clean_proj = sanitize_path(project_path)
        clean_data = sanitize_path(data_path)

        aprx = arcpy.mp.ArcGISProject(clean_proj)
        try:
            target_map = None
            for m in aprx.listMaps():
                if m.name.lower() == map_name.lower():
                    target_map = m
                    break
            if not target_map:
                return {"success": False, "error": f"Map '{map_name}' not found."}

            target_map.addDataFromPath(clean_data)

            if save_copy_path:
                clean_save = sanitize_path(save_copy_path)
                aprx.saveACopy(clean_save)
                out_project = clean_save
            else:
                try:
                    aprx.save()
                    out_project = clean_proj
                except OSError:
                    code_lines = [
                        f"m = [m for m in aprx.listMaps() if m.name.lower() == {repr(target_map.name.lower())}][0]",
                        f"m.addDataFromPath({repr(clean_data)})",
                    ]
                    stage_file = stage_ai_live_action(clean_proj, code_lines)
                    return {
                        "success": False,
                        "error": (
                            f"ArcGIS Pro has '{clean_proj}' open and locked. Staged action to 'ai_live_action.py'. "
                            f"Run 'Run AI Live Task' in ArcGIS Pro to apply changes live without file conflicts."
                        ),
                        "staged_file": stage_file,
                    }

            return {
                "success": True,
                "message": f"Successfully added {clean_data} to map '{target_map.name}'.",
                "saved_project": out_project,
            }
        finally:
            target_map = None
            m = None
            aprx = None
            gc.collect()

    @staticmethod
    def set_basemap(
        project_path: str,
        basemap_name: str,
        map_name: Optional[str] = None,
        custom_url: Optional[str] = None,
        save_copy_path: Optional[str] = None,
        export_lyrx: bool = False,
    ) -> Dict[str, Any]:
        """Changes the basemap of a project map to a built-in gallery basemap or custom XYZ tile service."""
        clean_proj = sanitize_path(project_path)
        if not os.path.isfile(clean_proj):
            return {"success": False, "error": f"Project file not found at: {clean_proj}"}

        aprx = arcpy.mp.ArcGISProject(clean_proj)
        try:
            maps = aprx.listMaps()
            if not maps:
                return {"success": False, "error": "No maps found in project."}

            target_map = None
            if map_name:
                for m in maps:
                    if m.name.lower() == map_name.lower():
                        target_map = m
                        break
                if not target_map:
                    return {"success": False, "error": f"Map '{map_name}' not found."}
            else:
                target_map = maps[0]

            norm_name = basemap_name.strip().lower()
            is_custom = bool(custom_url) or (norm_name in KNOWN_CUSTOM_BASEMAPS)
            tile_url = custom_url or KNOWN_CUSTOM_BASEMAPS.get(norm_name)

            removed_layers = []
            for lyr in target_map.listLayers():
                if getattr(lyr, "isBasemapLayer", False):
                    removed_layers.append(lyr.name)
                    target_map.removeLayer(lyr)

            if is_custom and tile_url:
                new_layer = target_map.addDataFromPath(tile_url)
                if new_layer:
                    new_layer.name = basemap_name
                    try:
                        cim = new_layer.getDefinition("V3")
                        cim.layerType = "BasemapBackground"
                        cim.name = basemap_name
                        new_layer.setDefinition(cim)
                    except Exception:
                        pass
            else:
                resolved_name = BUILTIN_BASEMAPS.get(norm_name, basemap_name)
                target_map.addBasemap(resolved_name)

            lyrx_path = None
            project_dir = os.path.dirname(os.path.abspath(clean_proj))
            if export_lyrx:
                lyrx_path = os.path.join(project_dir, "Active_Basemap.lyrx")
                for lyr in target_map.listLayers():
                    if getattr(lyr, "isBasemapLayer", False):
                        try:
                            lyr.saveACopy(lyrx_path)
                            break
                        except Exception:
                            pass

            state_file = os.path.join(project_dir, "active_basemap_state.json")
            try:
                state = {}
                if os.path.exists(state_file):
                    try:
                        with open(state_file, "r", encoding="utf-8") as f:
                            state = json.load(f)
                    except Exception:
                        pass
                state.update({
                    "basemap_name": basemap_name,
                    "is_custom": is_custom,
                    "tile_url": tile_url,
                    "map_name": target_map.name,
                    "project_path": clean_proj,
                    "lyrx_path": lyrx_path,
                    "timestamp": time.time(),
                })
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
            except Exception:
                pass

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
                    if is_custom and tile_url:
                        code_lines = [
                            f"m = [m for m in aprx.listMaps() if m.name.lower() == {repr(target_map.name.lower())}][0]",
                            "for lyr in m.listLayers():",
                            "    if getattr(lyr, 'isBasemapLayer', False):",
                            "        m.removeLayer(lyr)",
                            f"new_lyr = m.addDataFromPath({repr(tile_url)})",
                            f"if new_lyr: new_lyr.name = {repr(basemap_name)}",
                        ]
                    else:
                        code_lines = [
                            f"m = [m for m in aprx.listMaps() if m.name.lower() == {repr(target_map.name.lower())}][0]",
                            "for lyr in m.listLayers():",
                            "    if getattr(lyr, 'isBasemapLayer', False):",
                            "        m.removeLayer(lyr)",
                            f"m.addBasemap({repr(resolved_name)})",
                        ]
                    stage_file = stage_ai_live_action(clean_proj, code_lines)
                    return {
                        "success": False,
                        "error": (
                            f"ArcGIS Pro has '{clean_proj}' open and locked. Staged action to 'ai_live_action.py'. "
                            f"Run 'Run AI Live Task' in ArcGIS Pro to apply changes live without file conflicts."
                        ),
                        "staged_file": stage_file,
                        "map_name": target_map.name,
                        "basemap_applied": basemap_name,
                    }

            return {
                "success": True,
                "map_name": target_map.name,
                "basemap_applied": basemap_name,
                "is_custom_xyz": is_custom,
                "removed_layers": removed_layers,
                "saved_project": saved_path,
                "lyrx_exported": lyrx_path,
            }
        finally:
            target_map = None
            m = None
            lyr = None
            new_layer = None
            aprx = None
            gc.collect()

    @staticmethod
    def set_map_spatial_reference(
        project_path: str,
        epsg_code: int,
        map_name: Optional[str] = None,
        save_copy_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sets the spatial reference (coordinate system / EPSG) of a project map."""
        clean_proj = sanitize_path(project_path)
        if not os.path.isfile(clean_proj):
            return {"success": False, "error": f"Project file not found at: {clean_proj}"}

        sr = arcpy.SpatialReference(int(epsg_code))
        if not sr or not sr.name:
            return {"success": False, "error": f"Invalid EPSG code: {epsg_code}"}

        aprx = arcpy.mp.ArcGISProject(clean_proj)
        try:
            maps = aprx.listMaps()
            if not maps:
                return {"success": False, "error": "No maps found in project."}

            target_map = None
            if map_name:
                for m in maps:
                    if m.name.lower() == map_name.lower():
                        target_map = m
                        break
                if not target_map:
                    return {"success": False, "error": f"Map '{map_name}' not found."}
            else:
                target_map = maps[0]

            prev_sr = target_map.spatialReference.name
            prev_code = target_map.spatialReference.factoryCode

            target_map.spatialReference = sr

            project_dir = os.path.dirname(os.path.abspath(clean_proj))

            state_file = os.path.join(project_dir, "active_basemap_state.json")
            try:
                state = {}
                if os.path.exists(state_file):
                    with open(state_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                state["spatial_reference"] = {
                    "factory_code": sr.factoryCode,
                    "name": sr.name,
                    "type": sr.type,
                    "linear_unit": sr.linearUnitName,
                }
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
            except Exception:
                pass

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
                        f"m.spatialReference = arcpy.SpatialReference({int(sr.factoryCode)})",
                    ]
                    stage_file = stage_ai_live_action(clean_proj, code_lines)
                    return {
                        "success": False,
                        "error": (
                            f"ArcGIS Pro has '{clean_proj}' open and locked. Staged action to 'ai_live_action.py'. "
                            f"Run 'Run AI Live Task' in ArcGIS Pro to apply changes live without file conflicts."
                        ),
                        "staged_file": stage_file,
                        "map_name": target_map.name,
                        "new_spatial_reference": {
                            "name": sr.name,
                            "factory_code": sr.factoryCode,
                        },
                    }

            return {
                "success": True,
                "map_name": target_map.name,
                "previous_spatial_reference": f"{prev_sr} (EPSG:{prev_code})",
                "new_spatial_reference": {
                    "name": sr.name,
                    "factory_code": sr.factoryCode,
                    "type": sr.type,
                    "linear_unit_name": sr.linearUnitName,
                },
                "saved_project": saved_path,
            }
        finally:
            target_map = None
            m = None
            sr = None
            aprx = None
            gc.collect()
