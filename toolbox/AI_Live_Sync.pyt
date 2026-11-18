# -*- coding: utf-8 -*-
"""ArcGIS Pro Python Toolbox (PYT) for AI Live Synchronization.

Executes staged actions from ai_live_action.py in the active ArcGIS Pro session
using arcpy.mp.ArcGISProject("CURRENT") and refreshes the map view live.
"""

from __future__ import annotations
import os
import sys
import traceback
from typing import Any, List
import arcpy


class Toolbox(object):
    """ArcGIS Pro Python Toolbox definition for AI Live Sync."""

    def __init__(self) -> None:
        self.label = "AI Live Sync Toolbox"
        self.alias = "ailivesync"
        self.description = (
            "Synchronizes ArcGIS Pro active map views with staged actions from "
            "the ArcGIS Pro MCP Server using arcpy.mp.ArcGISProject('CURRENT')."
        )
        self.tools = [RunAILiveTask]


class RunAILiveTask(object):
    """Executes staged ai_live_action.py script directly inside active ArcGIS Pro session."""

    def __init__(self) -> None:
        self.label = "Run AI Live Task"
        self.description = (
            "Executes staged Python actions from 'ai_live_action.py' in the active "
            "ArcGIS Pro GUI session and refreshes active views and TOC."
        )
        self.canRunInBackground = False

    def getParameterInfo(self) -> List[arcpy.Parameter]:
        # Parameter 0: Staged script path (Optional - defaults to searching project dir)
        param_script = arcpy.Parameter(
            displayName="Staged Action Script (ai_live_action.py)",
            name="action_script",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_script.filter.list = ["py"]

        # Parameter 1: Project File Path (Optional - defaults to CURRENT in Pro GUI)
        param_proj = arcpy.Parameter(
            displayName="Project File (.aprx)",
            name="project_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
        )
        param_proj.filter.list = ["aprx"]

        return [param_script, param_proj]

    def isLicensed(self) -> bool:
        return True

    def updateParameters(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def updateMessages(self, parameters: List[arcpy.Parameter]) -> None:
        return

    def execute(self, parameters: List[arcpy.Parameter], messages: Any) -> None:
        script_val = parameters[0].valueAsText if parameters and len(parameters) > 0 else None
        proj_val = parameters[1].valueAsText if parameters and len(parameters) > 1 else None

        # 1. Resolve APRX
        aprx = None
        if proj_val and os.path.isfile(proj_val):
            messages.addMessage(f"Opening project from path: {proj_val}")
            aprx = arcpy.mp.ArcGISProject(proj_val)
        else:
            try:
                messages.addMessage("Accessing active ArcGIS Pro session ('CURRENT')...")
                aprx = arcpy.mp.ArcGISProject("CURRENT")
            except Exception as e:
                messages.addErrorMessage(
                    f"Could not access 'CURRENT' project session. If running outside ArcGIS Pro GUI, "
                    f"please specify project_path parameter. Error: {e}"
                )
                return

        # 2. Locate ai_live_action.py
        target_script = None
        if script_val and os.path.isfile(script_val):
            target_script = script_val
        else:
            candidates = []
            if proj_val and os.path.isfile(proj_val):
                candidates.append(os.path.dirname(os.path.abspath(proj_val)))
            if hasattr(aprx, "homeFolder") and aprx.homeFolder:
                candidates.append(aprx.homeFolder)
            if hasattr(aprx, "filePath") and aprx.filePath:
                candidates.append(os.path.dirname(os.path.abspath(aprx.filePath)))
            candidates.append(os.getcwd())

            for folder in candidates:
                cand_path = os.path.join(folder, "ai_live_action.py")
                if os.path.isfile(cand_path):
                    target_script = cand_path
                    break

        if not target_script or not os.path.isfile(target_script):
            messages.addErrorMessage(
                "No 'ai_live_action.py' script found to execute. Please stage an action from MCP or specify the script path."
            )
            return

        messages.addMessage(f"Executing staged action script: {target_script}")

        try:
            with open(target_script, "r", encoding="utf-8") as f:
                code_text = f.read()
        except Exception as e:
            messages.addErrorMessage(f"Failed to read action script '{target_script}': {e}")
            return

        scope = {
            "arcpy": arcpy,
            "aprx": aprx,
            "target_project_path": proj_val,
            "__file__": target_script,
            "__name__": "__ailivesync__",
        }

        try:
            exec(compile(code_text, target_script, "exec"), scope)
            if "run_live_task" in scope and callable(scope["run_live_task"]):
                try:
                    scope["run_live_task"](aprx)
                except TypeError:
                    scope["run_live_task"]()
            messages.addMessage("Staged action executed successfully.")
        except Exception as e:
            messages.addErrorMessage(f"Error executing action script: {e}\n{traceback.format_exc()}")
            return

        try:
            arcpy.RefreshActiveView()
            arcpy.RefreshTOC()
            messages.addMessage("Active view and Table of Contents refreshed.")
        except Exception:
            pass

        # If project was opened from path (e.g. testing), save it
        if proj_val and os.path.isfile(proj_val):
            try:
                aprx.save()
                messages.addMessage(f"Saved changes to project: {proj_val}")
            except Exception:
                pass
