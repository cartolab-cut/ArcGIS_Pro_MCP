# -*- coding: utf-8 -*-
"""
AI Live Action: Staging script for ArcGIS Pro MCP Live Synchronization.
This file is dynamically populated by the ArcGIS Pro MCP Server when staging
modifications (symbology, layers, selections, view extents) for active ArcGIS Pro sessions.

Executed live in the active ArcGIS Pro GUI session via AI_Live_Sync.pyt -> "Run AI Live Task".
"""
import arcpy

arcpy.AddMessage("==================================================")
arcpy.AddMessage(">>> ArcGIS Pro MCP: AI Live Synchronization <<<")
arcpy.AddMessage("==================================================")

try:
    p = arcpy.mp.ArcGISProject("CURRENT")
    arcpy.AddMessage(f"Connected to active ArcGIS Pro session: {p.filePath or 'Current Project'}")
    arcpy.AddMessage("Ready for live synchronization tasks staged by MCP.")
except Exception as e:
    arcpy.AddWarning(f"No active ArcGIS Pro GUI session ('CURRENT') detected: {e}")
