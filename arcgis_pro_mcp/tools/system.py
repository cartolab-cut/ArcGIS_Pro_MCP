"""System and environment tools for ArcGIS Pro MCP Server."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..models import ManageExtensionRequest
from ..services.system_service import SystemService
from ..utils import arcpy_safe


@arcpy_safe
def get_arcgis_system_info() -> Dict[str, Any]:
    """Returns comprehensive system information about the active ArcGIS Pro environment,

    including version, license level, active workspaces, and available extensions.
    """
    return SystemService.get_system_info()


@arcpy_safe
def set_arcgis_environment(
    workspace: Optional[str] = None,
    scratch_workspace: Optional[str] = None,
    overwrite_output: Optional[bool] = None,
    output_coordinate_system_wkid: Optional[int] = None,
    parallel_processing_factor: Optional[str] = None,
) -> Dict[str, Any]:
    """Updates global ArcGIS geoprocessing environment variables.

    Parameters:
        workspace: Path to primary geodatabase or folder workspace.
        scratch_workspace: Path to scratch workspace.
        overwrite_output: Whether to overwrite existing datasets (True/False).
        output_coordinate_system_wkid: WKID / EPSG code for output geometries (e.g. 4326 for WGS84, 3857 for Web Mercator).
        parallel_processing_factor: Parallel processing setting (e.g., '50%', '0', '4').
    """
    return SystemService.set_environment(
        workspace=workspace,
        scratch_workspace=scratch_workspace,
        overwrite_output=overwrite_output,
        output_coordinate_system_wkid=output_coordinate_system_wkid,
        parallel_processing_factor=parallel_processing_factor,
    )


@arcpy_safe
def manage_extension(
    extension_name: str,
    action: str = "check_out",
) -> Dict[str, Any]:
    """Manages an ArcGIS Pro extension license (check status, check out, or check in).

    Parameters:
        extension_name: Name of extension (e.g. 'Spatial', '3D', 'Network', 'ImageAnalyst').
        action: One of 'status', 'check_out', 'check_in'.
    """
    req = ManageExtensionRequest(
        extension_name=extension_name,
        action=action,
    )
    return SystemService.manage_extension(
        extension_name=req.extension_name,
        action=req.action,
    )
