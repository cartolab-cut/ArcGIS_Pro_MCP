# AI Live Synchronization for ArcGIS Pro

This toolbox (`AI_Live_Sync.pyt`) enables instantaneous, conflict-free synchronization between the **ArcGIS Pro MCP Server** and your active **ArcGIS Pro Desktop** session.

---

## Why AI Live Sync?

When an ArcGIS Pro desktop project (`.aprx`) is actively open, ArcGIS Pro places an exclusive file lock on the `.aprx` database. Direct disk writes to the project file from background processes can either fail with `OSError: Permission denied` or corrupt open maps.

Instead of writing conflicting duplicate files (like `<ProjectName>_updated.aprx`) or requiring you to restart ArcGIS Pro, the MCP server stages commands into `ai_live_action.py` using `arcpy.mp.ArcGISProject("CURRENT")`.

Running **Run AI Live Task** executes these staged commands directly inside the active GUI session and immediately refreshes the active map view (`arcpy.RefreshActiveView()`, `arcpy.RefreshTOC()`).

---

## Quick Setup (Pin to ArcGIS Pro Quick Access Toolbar)

1. Open **ArcGIS Pro**.
2. In the **Catalog Pane**, expand **Toolboxes** (or right-click Toolboxes > **Add Toolbox...**).
3. Browse to and select `AI_Live_Sync.pyt` from this directory.
4. Expand `AI_Live_Sync.pyt` to reveal **Run AI Live Task**.
5. Right-click **Run AI Live Task** and select **Add to Quick Access Toolbar**.

A single-click button will appear on the top-left title bar of ArcGIS Pro.

---

## How It Works

1. **MCP Stages Action**: When you ask Claude / AI assistant to change symbology, switch basemaps, or adjust coordinate systems while your project is open, MCP stages the Python code in `ai_live_action.py`.
2. **Execute Live**: Click **Run AI Live Task** in your ArcGIS Pro toolbar (or run it from the Catalog pane with default parameters).
3. **Instant Rendering**: Symbology, layers, and view extents update live in your active map view with zero downtime and zero file conflicts.
