"""MCP Resource handlers providing contextual ArcGIS Pro data."""

from __future__ import annotations
import json
from typing import Any, Dict
import arcpy
from .tools.system import get_arcgis_system_info


def get_system_info_resource() -> str:
    """Returns detailed JSON about the ArcGIS Pro runtime environment and license."""
    info = get_arcgis_system_info()
    return json.dumps(info, indent=2)


def get_available_toolboxes_resource() -> str:
    """Returns a list of all active geoprocessing toolboxes accessible via ArcPy."""
    toolboxes = [
        {"name": "analysis", "alias": "analysis", "description": "Spatial Analysis Tools (Buffer, Clip, Intersect, Spatial Join)"},
        {"name": "management", "alias": "management", "description": "Data Management Tools (Feature Class, Table, Fields, Projections)"},
        {"name": "conversion", "alias": "conversion", "description": "Format Conversion Tools (JSON, GeoJSON, CAD, Shapefiles, KML)"},
        {"name": "sa", "alias": "sa", "description": "Spatial Analyst (Map Algebra, Hydrology, Surface, Interpolation)"},
        {"name": "ddd", "alias": "ddd", "description": "3D Analyst Tools (TIN, Terrain, Hillshade, Slope, Contours)"},
        {"name": "cartography", "alias": "cartography", "description": "Cartography & Generalization Tools"},
        {"name": "stats", "alias": "stats", "description": "Spatial Statistics Tools (Hotspot Analysis, Clustering)"},
        {"name": "mp", "alias": "mp", "description": "ArcGIS Pro Mapping Automation Module (Projects, Maps, Layouts)"},
        {"name": "da", "alias": "da", "description": "Data Access Module (SearchCursor, InsertCursor, UpdateCursor, Describe)"},
    ]
    return json.dumps({"toolboxes": toolboxes}, indent=2)


def get_environment_settings_resource() -> str:
    """Returns the current state of arcpy.env settings."""
    settings = {
        "workspace": str(arcpy.env.workspace),
        "scratchWorkspace": str(arcpy.env.scratchWorkspace),
        "scratchGDB": str(arcpy.env.scratchGDB),
        "scratchFolder": str(arcpy.env.scratchFolder),
        "overwriteOutput": bool(arcpy.env.overwriteOutput),
        "parallelProcessingFactor": str(arcpy.env.parallelProcessingFactor),
        "geographicTransformations": str(arcpy.env.geographicTransformations),
    }
    return json.dumps({"arcgis_environments": settings}, indent=2)
