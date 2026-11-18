# ArcGIS Pro MCP Project Rules

## 1. Python Environment
- Always use the official ArcGIS Pro Conda Python environment for running tests, scripts, or the MCP server:
  `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`
- Never invoke system `python` or generic virtualenvs for ArcPy operations, as `arcpy` will not be found.
- Ensure `PYTHONIOENCODING=utf-8` is set when running Python commands.

## 2. Active Project Operations & Symbology Rules
- **Never Duplicate Projects**: Never create duplicate or updated project files (e.g., `<ProjectName>_updated.aprx`). When asked to modify the active project, target ONLY the active project.
- **On-the-Fly Symbology (No Unprompted .lyrx Files)**: Do not generate `.lyrx` files when changing layer symbology. Symbology must be updated on the fly directly on the layer in the active project. Only generate a `.lyrx` file when the user explicitly requests to "make a new layer".
- **Live Synchronization via AI_Live_Sync**:
  - Stage active session modifications (symbology, selections, view extents) in `ai_live_action.py` using `arcpy.mp.ArcGISProject("CURRENT")`.
  - Synchronize live into ArcGIS Pro by triggering `AI_Live_Sync.pyt` (**Run AI Live Task**) so results render immediately in the active map view without restarts or file conflicts.

## 3. Tool Architecture & Testing
- New MCP tools must be exposed in `arcgis_pro_mcp/tools/__init__.py` and included in `__all__`.
- Always verify tool additions and geoprocessing functionality by running:
  `& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_server.py`
