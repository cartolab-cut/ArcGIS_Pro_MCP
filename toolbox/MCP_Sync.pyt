# -*- coding: utf-8 -*-
"""ArcGIS Pro Python Toolbox (PYT) for live MCP Server Synchronization.

Allows applying basemaps, spatial references, and layer styling (.lyrx)
directly to the active ArcGIS Pro session without restarting the application.
"""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import arcpy


class Toolbox(object):
    """ArcGIS Pro Python Toolbox definition."""

    def __init__(self) -> None:
        self.label = "MCP Live Sync Toolbox"
        self.alias = "mcpsync"
        self.description = (
            "Synchronizes ArcGIS Pro active map views with external Model Context Protocol "
            "(MCP) server changes without requiring application restarts."
        )
        self.tools = [SyncBasemapAndCRS, ApplyLyrxToActiveMap, SyncAllFromMCP]


class SyncBasemapAndCRS(object):
    """Synchronizes active basemap and coordinate system from MCP state file."""

    def __init__(self) -> None:
        self.label = "Sync Basemap and Coordinate System"
        self.description = (
            "Reads active_basemap_state.json created by the MCP server and updates "
            "the active map's basemap and spatial reference live."
        )
        self.canRunInBackground = False

    def getParameterInfo(self) -> List[arcpy.Parameter]:
        # Parameter 0: State File Path (Optional - defaults to searching project dir)
        param_state = arcpy.Parameter(
            displayName="State JSON File",
            name="state_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_state.filter.list = ["json"]

        # Parameter 1: Target Map Name (Optional - defaults to active or first map)
        param_map = arcpy.Parameter(
            displayName="Target Map Name",
            name="target_map_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )

        # Parameter 2: Project File Path (Optional - defaults to CURRENT in Pro GUI)
        param_proj = arcpy.Parameter(
            displayName="Project File (.aprx)",
            name="project_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_proj.filter.list = ["aprx"]

        return [param_state, param_map, param_proj]

    def isLicensed(self) -> bool:
        return True

    def updateParameters(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def updateMessages(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def execute(self, parameters: List[arcpy.Parameter], messages: Any) -> None:
        state_file_val = parameters[0].valueAsText
        map_name_val = parameters[1].valueAsText
        proj_path_val = parameters[2].valueAsText

        # 1. Resolve ArcGIS Pro project
        aprx = None
        if proj_path_val and os.path.isfile(proj_path_val):
            messages.addMessage(f"Opening project from path: {proj_path_val}")
            aprx = arcpy.mp.ArcGISProject(proj_path_val)
        else:
            try:
                messages.addMessage("Accessing active ArcGIS Pro session (CURRENT)...")
                aprx = arcpy.mp.ArcGISProject("CURRENT")
            except Exception as e:
                messages.addErrorMessage(
                    f"Could not access 'CURRENT' project session. If running outside ArcGIS Pro GUI, "
                    f"please specify a valid .aprx in the project_path parameter. Error: {e}"
                )
                return

        # 2. Locate active_basemap_state.json
        state_file = None
        if state_file_val and os.path.isfile(state_file_val):
            state_file = state_file_val
        else:
            # Check project home folder, file directory, or current directory
            search_dirs = []
            if proj_path_val and os.path.isfile(proj_path_val):
                search_dirs.append(os.path.dirname(os.path.abspath(proj_path_val)))
            if hasattr(aprx, "homeFolder") and aprx.homeFolder:
                search_dirs.append(aprx.homeFolder)
            if hasattr(aprx, "filePath") and aprx.filePath:
                search_dirs.append(os.path.dirname(os.path.abspath(aprx.filePath)))
            search_dirs.append(os.getcwd())

            for d in search_dirs:
                candidate = os.path.join(d, "active_basemap_state.json")
                if os.path.isfile(candidate):
                    state_file = candidate
                    break

        if not state_file or not os.path.isfile(state_file):
            messages.addErrorMessage(
                "Could not find 'active_basemap_state.json'. Please execute 'set_basemap' or "
                "'set_map_spatial_reference' via MCP first, or specify the file manually."
            )
            return

        messages.addMessage(f"Reading state configuration from: {state_file}")
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
        except Exception as e:
            messages.addErrorMessage(f"Failed to parse state file JSON: {e}")
            return

        # 3. Resolve target map
        target_map = None
        maps = aprx.listMaps()
        if not maps:
            messages.addErrorMessage("No maps found in the target project.")
            return

        chosen_name = map_name_val or state_data.get("map_name")
        if chosen_name:
            for m in maps:
                if m.name.lower() == chosen_name.lower():
                    target_map = m
                    break

        if not target_map:
            target_map = getattr(aprx, "activeMap", None) or maps[0]

        messages.addMessage(f"Target map view: '{target_map.name}'")

        # 4. Sync Basemap
        basemap_name = state_data.get("basemap_name")
        is_custom = state_data.get("is_custom", False)
        tile_url = state_data.get("tile_url")

        if basemap_name or tile_url:
            messages.addMessage(f"Synchronizing Basemap -> '{basemap_name or tile_url}'...")
            # Remove existing basemap layers
            for lyr in target_map.listLayers():
                if getattr(lyr, "isBasemapLayer", False):
                    messages.addMessage(f"  Removing previous basemap layer: {lyr.name}")
                    target_map.removeLayer(lyr)

            if is_custom and tile_url:
                new_layer = target_map.addDataFromPath(tile_url)
                if new_layer:
                    new_layer.name = basemap_name or "Custom Basemap"
                    try:
                        cim = new_layer.getDefinition("V3")
                        cim.layerType = "BasemapBackground"
                        cim.name = new_layer.name
                        new_layer.setDefinition(cim)
                    except Exception:
                        pass
                messages.addMessage("  Custom XYZ tile basemap added.")
            elif basemap_name:
                builtin_mapping = {
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
                resolved = builtin_mapping.get(basemap_name.strip().lower(), basemap_name)
                target_map.addBasemap(resolved)
                messages.addMessage(f"  Gallery basemap '{resolved}' applied.")

        # 5. Sync Spatial Reference (Coordinate System)
        sr_info = state_data.get("spatial_reference")
        if sr_info and isinstance(sr_info, dict):
            factory_code = sr_info.get("factory_code")
            if factory_code:
                messages.addMessage(f"Synchronizing Coordinate System -> EPSG:{factory_code} ({sr_info.get('name')})...")
                new_sr = arcpy.SpatialReference(int(factory_code))
                target_map.spatialReference = new_sr
                messages.addMessage(f"  Spatial reference updated to: {new_sr.name}")

        # 6. Save changes if project path was supplied or running in session
        try:
            aprx.save()
            messages.addMessage("Saved project updates successfully.")
        except Exception as e:
            messages.addMessage(f"Live active view updated in memory ({e}).")

        messages.addMessage("Live MCP synchronization completed successfully!")


class ApplyLyrxToActiveMap(object):
    """Applies an exported layer file (.lyrx) to the active map view."""

    def __init__(self) -> None:
        self.label = "Apply Layer File (.lyrx) to Active Map"
        self.description = (
            "Loads a .lyrx layer file (such as Active_Basemap.lyrx or styled layer) "
            "directly into the active ArcGIS Pro map view."
        )
        self.canRunInBackground = False

    def getParameterInfo(self) -> List[arcpy.Parameter]:
        param_lyrx = arcpy.Parameter(
            displayName="Layer File (.lyrx)",
            name="lyrx_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_lyrx.filter.list = ["lyrx"]

        param_map = arcpy.Parameter(
            displayName="Target Map Name",
            name="target_map_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )

        param_as_basemap = arcpy.Parameter(
            displayName="Replace Existing Basemap",
            name="as_basemap",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        param_as_basemap.value = True

        param_proj = arcpy.Parameter(
            displayName="Project File (.aprx)",
            name="project_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_proj.filter.list = ["aprx"]

        return [param_lyrx, param_map, param_as_basemap, param_proj]

    def isLicensed(self) -> bool:
        return True

    def updateParameters(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def updateMessages(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def execute(self, parameters: List[arcpy.Parameter], messages: Any) -> None:
        lyrx_file_val = parameters[0].valueAsText
        map_name_val = parameters[1].valueAsText
        as_basemap = bool(parameters[2].value)
        proj_path_val = parameters[3].valueAsText

        # 1. Resolve project
        aprx = None
        if proj_path_val and os.path.isfile(proj_path_val):
            aprx = arcpy.mp.ArcGISProject(proj_path_val)
        else:
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
            except Exception as e:
                messages.addErrorMessage(f"Could not access active project: {e}")
                return

        # 2. Resolve .lyrx file
        lyrx_file = None
        if lyrx_file_val and os.path.isfile(lyrx_file_val):
            lyrx_file = lyrx_file_val
        else:
            search_dirs = []
            if proj_path_val and os.path.isfile(proj_path_val):
                search_dirs.append(os.path.dirname(os.path.abspath(proj_path_val)))
            if hasattr(aprx, "homeFolder") and aprx.homeFolder:
                search_dirs.append(aprx.homeFolder)
            if hasattr(aprx, "filePath") and aprx.filePath:
                search_dirs.append(os.path.dirname(os.path.abspath(aprx.filePath)))
            search_dirs.append(os.getcwd())

            for d in search_dirs:
                st_cand = os.path.join(d, "active_basemap_state.json")
                if os.path.isfile(st_cand):
                    try:
                        with open(st_cand, "r", encoding="utf-8") as f:
                            st_d = json.load(f)
                            cand_lyrx = st_d.get("lyrx_path")
                            if cand_lyrx and os.path.isfile(cand_lyrx):
                                lyrx_file = cand_lyrx
                                break
                    except Exception:
                        pass
                if lyrx_file:
                    break

            if not lyrx_file:
                for d in search_dirs:
                    candidate = os.path.join(d, "Active_Basemap.lyrx")
                    if os.path.isfile(candidate):
                        lyrx_file = candidate
                        break

        if not lyrx_file or not os.path.isfile(lyrx_file):
            messages.addErrorMessage(
                "Could not find layer file (.lyrx). Please specify the file or ensure "
                "'Active_Basemap.lyrx' exists in the project folder."
            )
            return

        # 3. Resolve map
        maps = aprx.listMaps()
        if not maps:
            messages.addErrorMessage("No maps in project.")
            return

        target_map = None
        if map_name_val:
            for m in maps:
                if m.name.lower() == map_name_val.lower():
                    target_map = m
                    break
        if not target_map:
            target_map = getattr(aprx, "activeMap", None) or maps[0]

        messages.addMessage(f"Applying layer file '{os.path.basename(lyrx_file)}' to '{target_map.name}'...")

        if as_basemap:
            for lyr in target_map.listLayers():
                if getattr(lyr, "isBasemapLayer", False):
                    messages.addMessage(f"  Removing previous basemap layer: {lyr.name}")
                    target_map.removeLayer(lyr)

        # Add lyrx to map
        new_layer = target_map.addDataFromPath(lyrx_file)
        if as_basemap and new_layer:
            try:
                cim = new_layer.getDefinition("V3")
                cim.layerType = "BasemapBackground"
                cim.name = new_layer.name
                new_layer.setDefinition(cim)
            except Exception:
                pass
        messages.addMessage(f"Layer '{getattr(new_layer, 'name', os.path.basename(lyrx_file))}' successfully added.")

        # Save changes if project path was supplied or running in session
        try:
            aprx.save()
            messages.addMessage("Saved project updates successfully.")
        except Exception as e:
            messages.addMessage(f"Live active view updated in memory ({e}).")


class SyncAllFromMCP(object):
    """One-click master tool to synchronize state JSON, layer files, and CRS."""

    def __init__(self) -> None:
        self.label = "Sync All MCP Changes"
        self.description = (
            "Performs a full live synchronization: updates basemap, coordinate system, "
            "and styling from active MCP state files into the open ArcGIS Pro session."
        )
        self.canRunInBackground = False

    def getParameterInfo(self) -> List[arcpy.Parameter]:
        param_proj = arcpy.Parameter(
            displayName="Project File (.aprx)",
            name="project_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_proj.filter.list = ["aprx"]

        param_map = arcpy.Parameter(
            displayName="Target Map Name",
            name="target_map_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )

        param_state = arcpy.Parameter(
            displayName="State JSON File",
            name="state_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_state.filter.list = ["json"]

        param_lyrx = arcpy.Parameter(
            displayName="Layer File (.lyrx)",
            name="lyrx_file",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_lyrx.filter.list = ["lyrx"]

        return [param_proj, param_map, param_state, param_lyrx]

    def isLicensed(self) -> bool:
        return True

    def updateParameters(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def updateMessages(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def execute(self, parameters: List[arcpy.Parameter], messages: Any) -> None:
        messages.addMessage("Starting Full MCP Live Synchronization...")
        proj_path_val = parameters[0].valueAsText
        map_name_val = parameters[1].valueAsText
        state_file_val = parameters[2].valueAsText
        lyrx_file_val = parameters[3].valueAsText

        # 1. Resolve project
        aprx = None
        if proj_path_val and os.path.isfile(proj_path_val):
            messages.addMessage(f"Opening project from path: {proj_path_val}")
            aprx = arcpy.mp.ArcGISProject(proj_path_val)
        else:
            try:
                messages.addMessage("Accessing active ArcGIS Pro session (CURRENT)...")
                aprx = arcpy.mp.ArcGISProject("CURRENT")
            except Exception as e:
                messages.addErrorMessage(
                    f"Could not access 'CURRENT' project session. If running outside ArcGIS Pro GUI, "
                    f"please specify a valid .aprx in the project_path parameter. Error: {e}"
                )
                return

        # 2. Resolve target map
        maps = aprx.listMaps()
        if not maps:
            messages.addErrorMessage("No maps found in project.")
            return

        target_map = None
        if map_name_val:
            for m in maps:
                if m.name.lower() == map_name_val.lower():
                    target_map = m
                    break
        if not target_map:
            target_map = getattr(aprx, "activeMap", None) or maps[0]

        messages.addMessage(f"Target map view: '{target_map.name}'")

        # 3. Build search directories
        search_dirs = []
        if proj_path_val and os.path.isfile(proj_path_val):
            search_dirs.append(os.path.dirname(os.path.abspath(proj_path_val)))
        if hasattr(aprx, "homeFolder") and aprx.homeFolder:
            search_dirs.append(aprx.homeFolder)
        if hasattr(aprx, "filePath") and aprx.filePath:
            search_dirs.append(os.path.dirname(os.path.abspath(aprx.filePath)))
        search_dirs.append(os.getcwd())

        # 4. Locate state file
        state_file = None
        if state_file_val and os.path.isfile(state_file_val):
            state_file = state_file_val
        else:
            for d in search_dirs:
                candidate = os.path.join(d, "active_basemap_state.json")
                if os.path.isfile(candidate):
                    state_file = candidate
                    break

        synced_anything = False
        state_data: Dict[str, Any] = {}

        if state_file and os.path.isfile(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                messages.addMessage(f"Reading state configuration from: {state_file}")

                # Basemap
                basemap_name = state_data.get("basemap_name")
                is_custom = state_data.get("is_custom", False)
                tile_url = state_data.get("tile_url")

                if basemap_name or tile_url:
                    messages.addMessage(f"Synchronizing Basemap -> '{basemap_name or tile_url}'...")
                    for lyr in target_map.listLayers():
                        if getattr(lyr, "isBasemapLayer", False):
                            target_map.removeLayer(lyr)

                    if is_custom and tile_url:
                        new_layer = target_map.addDataFromPath(tile_url)
                        if new_layer:
                            new_layer.name = basemap_name or "Custom Basemap"
                            try:
                                cim = new_layer.getDefinition("V3")
                                cim.layerType = "BasemapBackground"
                                cim.name = new_layer.name
                                new_layer.setDefinition(cim)
                            except Exception:
                                pass
                        messages.addMessage("  Custom XYZ tile basemap added.")
                    elif basemap_name:
                        builtin_mapping = {
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
                        resolved = builtin_mapping.get(basemap_name.strip().lower(), basemap_name)
                        target_map.addBasemap(resolved)
                        messages.addMessage(f"  Gallery basemap '{resolved}' applied.")
                    synced_anything = True

                # Spatial Reference
                sr_info = state_data.get("spatial_reference")
                if sr_info and isinstance(sr_info, dict):
                    factory_code = sr_info.get("factory_code")
                    if factory_code:
                        messages.addMessage(f"Synchronizing Coordinate System -> EPSG:{factory_code}...")
                        new_sr = arcpy.SpatialReference(int(factory_code))
                        target_map.spatialReference = new_sr
                        messages.addMessage(f"  Spatial reference updated to: {new_sr.name}")
                        synced_anything = True
            except Exception as e:
                messages.addWarningMessage(f"Error processing state JSON: {e}")

        # 5. Locate and apply layer file (.lyrx)
        lyrx_file = None
        if lyrx_file_val and os.path.isfile(lyrx_file_val):
            lyrx_file = lyrx_file_val
        elif state_data.get("lyrx_path") and os.path.isfile(state_data["lyrx_path"]):
            lyrx_file = state_data["lyrx_path"]
        else:
            for d in search_dirs:
                candidate = os.path.join(d, "Active_Basemap.lyrx")
                if os.path.isfile(candidate):
                    lyrx_file = candidate
                    break

        if lyrx_file and os.path.isfile(lyrx_file):
            messages.addMessage(f"Applying layer file from: {lyrx_file}")
            is_active_bm = "active_basemap" in os.path.basename(lyrx_file).lower()
            if is_active_bm:
                for lyr in target_map.listLayers():
                    if getattr(lyr, "isBasemapLayer", False):
                        target_map.removeLayer(lyr)

            new_layer = target_map.addDataFromPath(lyrx_file)
            if is_active_bm and new_layer:
                try:
                    cim = new_layer.getDefinition("V3")
                    cim.layerType = "BasemapBackground"
                    new_layer.setDefinition(cim)
                except Exception:
                    pass
            messages.addMessage(f"  Layer '{getattr(new_layer, 'name', os.path.basename(lyrx_file))}' added to map.")
            synced_anything = True

        if not synced_anything:
            messages.addWarningMessage(
                "Neither 'active_basemap_state.json' nor a valid .lyrx file was found to synchronize."
            )
        else:
            try:
                aprx.save()
                messages.addMessage("Saved project updates successfully.")
            except Exception as e:
                messages.addMessage(f"Live active view updated in memory ({e}).")

        messages.addMessage("MCP live sync process finished successfully.")
