"""Utility functions and formatting helpers for ArcGIS Pro MCP Server."""

from __future__ import annotations
from contextlib import contextmanager
import functools
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


def sanitize_path(path_str: str, base_dir: Optional[str] = None) -> str:
    """Normalizes and expands file system paths with traversal protection.

    Parameters:
        path_str: Path string to sanitize.
        base_dir: Optional root directory that path_str must stay within.
    """
    if not path_str:
        return ""
    if "\x00" in path_str:
        raise ValueError("Invalid path: contains null byte character.")
    # Strip any accidental wrapping quotes
    cleaned = path_str.strip().strip("'\"")
    expanded = os.path.expanduser(os.path.expandvars(cleaned))
    norm = os.path.normpath(expanded)
    effective_base = base_dir or os.environ.get("ARCGIS_BASE_DIR")
    if effective_base:
        abs_base = os.path.normcase(os.path.abspath(effective_base))
        abs_target = os.path.normcase(os.path.abspath(norm))
        if not (abs_target == abs_base or abs_target.startswith(abs_base + os.sep)):
            raise ValueError(f"Path traversal detected: '{path_str}' escapes base directory '{effective_base}'.")
    return norm


@contextmanager
def extension_scope(*extension_names: str):
    """Safely check out an ArcGIS Pro extension and guarantee check-in in a finally block.

    Supports candidate fallback extensions (e.g. extension_scope('Spatial', '3D')).
    Prevents license leaks on long-running MCP server sessions.
    """
    import arcpy
    checked_ext = None
    status = "Unavailable"
    try:
        for ext in extension_names:
            status = arcpy.CheckExtension(ext)
            if status == "Available":
                out_status = arcpy.CheckOutExtension(ext)
                if str(out_status).lower() in ("checkedout", "available"):
                    checked_ext = ext
                    break
        yield checked_ext or status
    finally:
        if checked_ext:
            try:
                arcpy.CheckInExtension(checked_ext)
            except Exception:
                pass


def parse_color_rgb(color: Any) -> Optional[Tuple[int, int, int]]:
    """Extracts (r, g, b) tuple (0-255) from hex string, RGB list, or CIM dict."""
    if not color:
        return None
    if isinstance(color, dict) and "RGB" in color:
        vals = color["RGB"]
        if len(vals) >= 3:
            return int(vals[0]), int(vals[1]), int(vals[2])
    if isinstance(color, (list, tuple)):
        if len(color) >= 3:
            return int(color[0]), int(color[1]), int(color[2])
    if isinstance(color, str):
        c = color.strip().lstrip("#")
        if len(c) in (6, 8):
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
            return r, g, b
    return None


def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculates relative luminance according to WCAG 2.1 specifications."""
    def _channel_lum(c_val: int) -> float:
        c = c_val / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r_lum = _channel_lum(rgb[0])
    g_lum = _channel_lum(rgb[1])
    b_lum = _channel_lum(rgb[2])
    return 0.2126 * r_lum + 0.7152 * g_lum + 0.0722 * b_lum


def calculate_contrast_ratio(color1: Any, color2: Any) -> float:
    """Calculates WCAG 2.1 contrast ratio between two colors (ranging 1.0 to 21.0)."""
    rgb1 = parse_color_rgb(color1) or (0, 0, 0)
    rgb2 = parse_color_rgb(color2) or (255, 255, 255)
    lum1 = calculate_luminance(rgb1)
    lum2 = calculate_luminance(rgb2)
    l_max = max(lum1, lum2)
    l_min = min(lum1, lum2)
    return round((l_max + 0.05) / (l_min + 0.05), 2)


def is_wcag_accessible(
    foreground_color: Any,
    background_color: Any = (255, 255, 255),
    min_ratio: float = 4.5,
) -> Dict[str, Any]:
    """Evaluates WCAG 2.1 color contrast compliance.

    Parameters:
        foreground_color: Hex, RGB list, or CIM dict of text/symbol.
        background_color: Background color (default: white [255, 255, 255]).
        min_ratio: Target contrast ratio (4.5 for normal text, 3.0 for large text/UI components).
    """
    ratio = calculate_contrast_ratio(foreground_color, background_color)
    return {
        "contrast_ratio": ratio,
        "is_accessible": ratio >= min_ratio,
        "wcag_aa_normal_text": ratio >= 4.5,
        "wcag_aa_large_or_graphic": ratio >= 3.0,
        "wcag_aaa_normal_text": ratio >= 7.0,
    }


def stage_ai_live_action(project_path: str, action_code_lines: List[str]) -> str:
    """Stages Python commands targeting arcpy.mp.ArcGISProject('CURRENT') into ai_live_action.py."""
    clean_path = sanitize_path(project_path)
    proj_dir = os.path.dirname(os.path.abspath(clean_path)) if clean_path else os.getcwd()
    stage_file = os.path.join(proj_dir, "ai_live_action.py")
    clean_path_repr = repr(clean_path)
    lines = [
        "# Auto-generated by ArcGIS Pro MCP Server for Live Synchronization",
        "# Run via AI_Live_Sync.pyt ('Run AI Live Task') in active ArcGIS Pro GUI session",
        "import arcpy",
        "",
        "def run_live_task(target_aprx=None):",
        "    if target_aprx is not None:",
        "        aprx = target_aprx",
        "    else:",
        "        try:",
        "            aprx = arcpy.mp.ArcGISProject('CURRENT')",
        "        except Exception:",
        "            aprx = globals().get('aprx')",
        "    if aprx is None and globals().get('target_project_path'):",
        "        aprx = arcpy.mp.ArcGISProject(globals().get('target_project_path'))",
        f"    elif aprx is None and {clean_path_repr}:",
        f"        aprx = arcpy.mp.ArcGISProject({clean_path_repr})",
    ]
    for line in action_code_lines:
        lines.append(f"    {line}")
    lines.extend([
        "    try:",
        "        arcpy.RefreshActiveView()",
        "        arcpy.RefreshTOC()",
        "    except Exception:",
        "        pass",
        "",
        "if __name__ == '__main__':",
        "    run_live_task()",
        "",
    ])
    with open(stage_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return stage_file


def capture_arcpy_messages(severity: int = 0) -> str:
    """Retrieves ArcPy geoprocessing messages safely."""
    try:
        import arcpy
        msgs = arcpy.GetMessages(severity)
        return msgs.strip() if msgs else ""
    except Exception:
        return ""


def format_spatial_reference(sr: Any) -> Optional[Dict[str, Any]]:
    """Converts an arcpy.SpatialReference object into a dictionary."""
    if sr is None:
        return None
    try:
        return {
            "name": getattr(sr, "name", "Unknown"),
            "factory_code": getattr(sr, "factoryCode", None),
            "type": getattr(sr, "type", "Unknown"),
            "linear_unit_name": getattr(sr, "linearUnitName", ""),
            "angular_unit_name": getattr(sr, "angularUnitName", ""),
            "is_geographic": getattr(sr, "type", "").lower() == "geographic",
            "is_projected": getattr(sr, "type", "").lower() == "projected",
        }
    except Exception:
        return {"name": str(sr)}


def format_extent(extent: Any) -> Optional[Dict[str, Any]]:
    """Converts an arcpy.Extent object into a dictionary."""
    if extent is None:
        return None
    try:
        return {
            "xmin": round(float(extent.XMin), 6),
            "ymin": round(float(extent.YMin), 6),
            "xmax": round(float(extent.XMax), 6),
            "ymax": round(float(extent.YMax), 6),
            "spatial_reference": format_spatial_reference(getattr(extent, "spatialReference", None)),
        }
    except Exception:
        return {"raw": str(extent)}


def arcpy_safe(func: Callable) -> Callable:
    """Decorator to catch arcpy ExecuteError and standard exceptions,

    returning structured error dictionaries instead of crashing.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            gp_messages = capture_arcpy_messages()
            error_data = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "geoprocessing_messages": gp_messages,
                "traceback": traceback.format_exc(),
            }
            return error_data
    return wrapper
