"""Configuration and environment detection for ArcGIS Pro MCP Server."""

from __future__ import annotations
import os
import sys
from pathlib import Path

# Package Metadata
SERVER_NAME = "ArcGIS_Pro_MCP"
SERVER_VERSION = "1.0.0"

# Execution & Security Flags
ENABLE_ARCPY_EXEC = os.environ.get("ENABLE_ARCPY_EXEC", "true").lower() in ("true", "1", "yes")

# ArcGIS Pro Path Defaults
DEFAULT_PRO_DIR = Path(r"C:\Program Files\ArcGIS\Pro")
DEFAULT_PRO_PYTHON_DIR = DEFAULT_PRO_DIR / "bin" / "Python"
DEFAULT_PRO_PY3_ENV = DEFAULT_PRO_PYTHON_DIR / "envs" / "arcgispro-py3"
DEFAULT_PRO_PYTHON_EXE = DEFAULT_PRO_PY3_ENV / "python.exe"
DEFAULT_PROPY_BAT = DEFAULT_PRO_PYTHON_DIR / "Scripts" / "propy.bat"


def get_arcgis_pro_install_dir() -> Path:
    """Detects ArcGIS Pro installation directory via registry or standard paths."""
    # 1. Environment variable override
    env_path = os.environ.get("ARCGISPRO_HOME")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    # 2. Check standard directory
    if DEFAULT_PRO_DIR.exists():
        return DEFAULT_PRO_DIR

    # 3. Registry lookup (Windows)
    try:
        import winreg
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(root, r"SOFTWARE\Esri\ArcGISPro", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                    install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                    if install_dir and Path(install_dir).exists():
                        return Path(install_dir)
            except OSError:
                pass
    except ImportError:
        pass

    return DEFAULT_PRO_DIR


def get_arcgis_python_executable() -> Path:
    """Returns the path to the active or default ArcGIS Pro Python executable."""
    # If running inside the ArcGIS Pro python environment, return current sys.executable
    if "arcgis" in sys.executable.lower() or "esri" in sys.executable.lower():
        return Path(sys.executable)

    # Check default path
    if DEFAULT_PRO_PYTHON_EXE.exists():
        return DEFAULT_PRO_PYTHON_EXE

    pro_dir = get_arcgis_pro_install_dir()
    candidate = pro_dir / "bin" / "Python" / "envs" / "arcgispro-py3" / "python.exe"
    if candidate.exists():
        return candidate

    return Path(sys.executable)
