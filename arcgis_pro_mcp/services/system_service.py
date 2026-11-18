"""System and environment service for ArcGIS Pro."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import arcpy

from ..utils import format_spatial_reference, sanitize_path


class SystemService:
    """Service layer encapsulating ArcGIS Pro environment, license, and system info."""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Returns version, build, license level, and environment configuration."""
        install_info = arcpy.GetInstallInfo()
        product_level = arcpy.ProductInfo()

        common_extensions = [
            "Spatial",
            "3D",
            "Network",
            "ImageAnalyst",
            "Geostatistical",
            "Airports",
            "Defense",
            "DataInteroperability",
        ]
        extension_status = {}
        for ext in common_extensions:
            extension_status[ext] = arcpy.CheckExtension(ext)

        return {
            "success": True,
            "product_name": install_info.get("ProductName", "ArcGIS Pro"),
            "version": install_info.get("Version", "Unknown"),
            "build_number": install_info.get("BuildNumber", "Unknown"),
            "install_dir": install_info.get("InstallDir", "Unknown"),
            "license_level": product_level,
            "environment": {
                "workspace": str(arcpy.env.workspace),
                "scratch_workspace": str(arcpy.env.scratchWorkspace),
                "scratch_gdb": str(arcpy.env.scratchGDB),
                "scratch_folder": str(arcpy.env.scratchFolder),
                "overwrite_output": bool(arcpy.env.overwriteOutput),
                "output_coordinate_system": format_spatial_reference(arcpy.env.outputCoordinateSystem),
                "parallel_processing_factor": str(arcpy.env.parallelProcessingFactor),
            },
            "extensions": extension_status,
        }

    @staticmethod
    def set_environment(
        workspace: Optional[str] = None,
        scratch_workspace: Optional[str] = None,
        overwrite_output: Optional[bool] = None,
        output_coordinate_system_wkid: Optional[int] = None,
        parallel_processing_factor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Updates global ArcPy geoprocessing environment variables."""
        updated = {}

        if workspace is not None:
            clean_ws = sanitize_path(workspace)
            arcpy.env.workspace = clean_ws
            updated["workspace"] = clean_ws

        if scratch_workspace is not None:
            clean_scratch = sanitize_path(scratch_workspace)
            arcpy.env.scratchWorkspace = clean_scratch
            updated["scratch_workspace"] = clean_scratch

        if overwrite_output is not None:
            arcpy.env.overwriteOutput = bool(overwrite_output)
            updated["overwrite_output"] = bool(overwrite_output)

        if output_coordinate_system_wkid is not None:
            sr = arcpy.SpatialReference(output_coordinate_system_wkid)
            arcpy.env.outputCoordinateSystem = sr
            updated["output_coordinate_system"] = format_spatial_reference(sr)

        if parallel_processing_factor is not None:
            arcpy.env.parallelProcessingFactor = parallel_processing_factor
            updated["parallel_processing_factor"] = parallel_processing_factor

        return {
            "success": True,
            "message": "Environment settings successfully updated.",
            "updated_settings": updated,
            "current_workspace": str(arcpy.env.workspace),
            "overwrite_output": bool(arcpy.env.overwriteOutput),
        }

    @staticmethod
    def manage_extension(
        extension_name: str,
        action: str = "check_out",
    ) -> Dict[str, Any]:
        """Manages ArcGIS Pro extension checkout, checkin, or status."""
        action_clean = action.lower()
        availability = arcpy.CheckExtension(extension_name)

        if action_clean == "status":
            return {
                "success": True,
                "extension": extension_name,
                "status": availability,
                "is_available": availability.lower() == "available",
            }

        if action_clean == "check_out":
            res = arcpy.CheckOutExtension(extension_name)
            return {
                "success": res.lower() == "checkedout",
                "extension": extension_name,
                "result": res,
                "message": (
                    f"Extension {extension_name} checked out."
                    if res.lower() == "checkedout"
                    else f"Failed to check out: {res}"
                ),
            }

        if action_clean == "check_in":
            res = arcpy.CheckInExtension(extension_name)
            return {
                "success": res.lower() == "checkedin",
                "extension": extension_name,
                "result": res,
                "message": f"Extension {extension_name} checked in.",
            }

        return {
            "success": False,
            "error": f"Invalid action '{action}'. Valid actions are 'status', 'check_out', 'check_in'.",
        }
