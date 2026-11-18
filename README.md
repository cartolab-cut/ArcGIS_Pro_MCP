# ArcGIS Pro Model Context Protocol (MCP) Server

[![Model Context Protocol](https://img.shields.io/badge/MCP-2.0+-blue.svg)](https://modelcontextprotocol.io)
[![ArcGIS Pro](https://img.shields.io/badge/ArcGIS%20Pro-3.7+-green.svg)](https://www.esri.com/en-us/arcgis/products/arcgis-pro/overview)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.0+-e92063.svg)](https://docs.pydantic.dev/)

An enterprise-grade **Model Context Protocol (MCP)** server that connects AI assistants (such as Claude Desktop, Antigravity, Cursor, and VS Code) directly to **ArcGIS Pro** and **ArcPy**.

It empowers LLMs to inspect `.aprx` projects, run geoprocessing analysis, configure map symbology & labeling, create and manage file geodatabases, query features via SQL, process elevation rasters (hillshade, slope, aspect, contours), and execute complex multi-step ArcPy automation scripts safely.

---

## 🌟 Key Features

- **Clean Architecture & Service Layer**: Complete separation of concerns between protocol adapters (`arcgis_pro_mcp/tools/`) and pure geospatial execution (`arcgis_pro_mcp/services/`), fully typed with **Pydantic v2** models and Enums.
- **Cartography & Symbology (`arcpy.mp`)**: Style layers using `SimpleRenderer` (custom colors, sizes, outlines), `UniqueValueRenderer` (categorical fields, color ramps), and `GraduatedColorsRenderer` (Jenks Natural Breaks, Quantile, Equal Interval), plus Arcade dynamic labeling and `.lyrx` export.
- **Zero-Restart Live Sync (`MCP_Sync.pyt`)**: Overcomes ArcGIS Pro `.aprx` file locking. Modify basemaps and coordinate systems via MCP, then apply changes instantly to the active map view in open desktop sessions using the included Python Toolbox.
- **Project & Map Automation**: Inspect `.aprx` projects, list map layers, view field schemas, add spatial data to maps, and export maps or layouts to high-res PNG, JPEG, PDF, or TIFF.
- **Geoprocessing & Spatial Analysis**: High-speed dedicated tools for Buffer, Clip, Intersect, Spatial Join, and Dissolve, plus a universal dynamic tool runner (`run_geoprocessing_tool`) for any ArcPy geoprocessing tool.
- **Geodatabase & Data Management**: Create File Geodatabases (`.gdb`), create point/line/polygon feature classes with custom spatial references (WKID/EPSG), inspect schemas, add fields, and convert between Shapefile, GDB, GeoJSON, and CSV.
- **Attribute Queries & Selections**: Query records with SQL `WHERE` clauses via fast `SearchCursor`, return structured records with optional Well-Known Text (WKT) geometries, select by location/attributes, and calculate summary statistics.
- **Raster & Surface Analysis (`arcpy.sa` / `arcpy.ddd`)**: Extract rasters by mask, generate hillshade, calculate slope/aspect, and generate elevation contour lines from DEMs.
- **Dynamic ArcPy Execution (`execute_arcpy_code`)**: Run multi-step custom Python/ArcPy scripts on the fly with captured `stdout`, `stderr`, and ESRI diagnostic messages.
- **Contextual Resources & Prompts**: Built-in prompts (`gis_spatial_analyst`, `geoprocessing_debugger`, `cartography_specialist`) and live resources (`arcgis://system/info`, `arcgis://system/toolboxes`, `arcgis://system/environments`).

---

## 📁 Repository Structure

```
ArcGIS_Pro_MCP/
├── arcgis_pro_mcp/
│   ├── __init__.py              # Package init
│   ├── server.py                # MCP Server instance and registration
│   ├── config.py                # Environment auto-detection
│   ├── resources.py             # Contextual MCP resources (info, toolboxes, envs)
│   ├── prompts.py               # Pre-built GIS workflow assistance prompts
│   ├── utils.py                 # Error handlers, spatial ref formatters, path sanitization
│   ├── models/                  # Pydantic v2 Models & Enums
│   │   ├── __init__.py          # Exported schemas and enums
│   │   ├── enums.py             # GeometryType, BasemapName, RendererType, etc.
│   │   └── schemas.py           # Request validation models
│   ├── services/                # Clean Architecture Service Layer
│   │   ├── __init__.py          # Service exports
│   │   ├── system_service.py    # Environment & license service
│   │   ├── project_service.py   # Project, map, basemap, and CRS service
│   │   ├── cartography_service.py # Symbology, renderers, labeling service
│   │   ├── gp_service.py        # Geoprocessing analysis service
│   │   ├── data_service.py      # Geodatabase & feature class service
│   │   ├── analysis_service.py  # Cursors, SQL queries, and statistics service
│   │   ├── raster_service.py    # Terrain, DEM, and surface service
│   │   └── scripting_service.py # Dynamic ArcPy script execution service
│   └── tools/                   # MCP Protocol Tool Adapters
│       ├── __init__.py          # Consolidated tool exports (39 tools)
│       ├── system.py            # Info, licenses, workspaces, extensions
│       ├── projects.py          # .aprx inspect, basemaps, CRS, export map
│       ├── cartography.py       # Symbology, renderers, labels, lyrx export
│       ├── geoprocessing.py     # Buffer, clip, intersect, spatial join, dissolve
│       ├── data_management.py   # GDB creation, feature classes, export, schema
│       ├── analysis.py          # Queries, select by attribute/location, statistics
│       ├── raster.py            # Raster algebra, hillshade, slope, aspect, contours
│       └── scripting.py         # Dynamic ArcPy code runner
├── toolbox/                     # ArcGIS Pro Python Toolbox
│   ├── MCP_Sync.pyt             # Live sync toolbox (CURRENT session zero-restart)
│   └── README_TOOLBOX.md        # Python Toolbox installation and usage guide
├── run_server.py                # Direct Python runner script
├── run_server.bat               # Windows batch launcher (auto-detects Pro Python)
├── run_server.ps1               # PowerShell launcher
├── test_server.py               # Comprehensive end-to-end integration test suite
├── claude_desktop_config.json   # Ready-to-use configuration for Claude Desktop
├── pyproject.toml               # Python packaging metadata
└── README.md                    # Documentation
```

---

## 🚀 Quick Start

### 1. Requirements

- **ArcGIS Pro** installed (ArcGIS Pro 3.0 or higher; tested on 3.7 with ArcInfo license).
- **Python MCP SDK & Pydantic**: Installed in your active ArcGIS Pro Python environment:
  ```powershell
  & "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pip install --user mcp pydantic
  ```

### 2. Verify Installation with the Test Suite

Run the integration test suite to verify tool registration and live ArcPy execution:

```powershell
$env:PYTHONIOENCODING="utf-8"
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_server.py
```

Expected output:
```
Ran 6 tests in 32.7s
OK
[PASS] Server initialized with 39 tools, 3 resources, and 3 prompts.
[PASS] Detected ArcGIS Pro version: 3.7, License: ArcInfo
[PASS] Created File GDB at ...
[PASS] Configured SimpleRenderer with hex color #FF5733 and size 14.
[PASS] Configured UniqueValueRenderer classified on field 'PointName'.
[PASS] Configured GraduatedColorsRenderer with 3 natural breaks on field 'Value'.
[PASS] Configured dynamic Arcade labels with expression '$feature.PointName'.
[PASS] Exported styled layer to Exported_SamplePoints.lyrx
[PASS] Applied symbology definition from .lyrx to target point layer.
[PASS] Pydantic v2 schemas and Clean Architecture service layer verified.
[PASS] Successfully imported MCP_Sync.pyt with tools: ['ApplyLyrxToActiveMap', 'SyncAllFromMCP', 'SyncBasemapAndCRS']
[PASS] Executed SyncBasemapAndCRS from MCP_Sync.pyt on test project.
```

### 3. Launching the MCP Server

You can launch the server using any of the following methods:

#### Method A: Direct Command Line
```powershell
$env:PYTHONIOENCODING="utf-8"
& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_server.py
```

#### Method B: Windows Batch Launcher
```cmd
run_server.bat
```

#### Method C: SSE / HTTP Network Transport
```cmd
run_server.bat --transport sse --host 127.0.0.1 --port 8000
```

---

## ⚙️ Client Configuration

### Claude Desktop

Add the following to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "arcgis-pro": {
      "command": "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe",
      "args": [
        "c:\\Pavlos_project's\\ArcGIS_Pro_MCP\\run_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Antigravity / Cursor / VS Code MCP

Add to your MCP settings or configuration file:

```json
{
  "mcpServers": {
    "arcgis-pro": {
      "command": "cmd.exe",
      "args": [
        "/c",
        "c:\\Pavlos_project's\\ArcGIS_Pro_MCP\\run_server.bat"
      ]
    }
  }
}
```

---

## 🛠️ Complete Tool Catalog (39 Tools)

### 1. System & Environment
| Tool | Description |
|---|---|
| `get_arcgis_system_info` | Returns version, build number, license level (Basic/Standard/Advanced), and active extension statuses. |
| `set_arcgis_environment` | Configures `arcpy.env` workspace, scratch workspace, overwriteOutput, and output coordinate system. |
| `manage_extension` | Checks availability, checks out, or checks in licenses for Spatial, 3D, Network, and other extensions. |

### 2. ArcGIS Pro Projects (`.aprx`), Maps & Basemaps
| Tool | Description |
|---|---|
| `inspect_project` | Catalogs all maps, layouts, default geodatabase, and default toolbox inside an `.aprx` project file. |
| `list_map_layers` | Lists all layers and tables in a map, visibility, data sources, and definition queries. |
| `get_layer_properties` | Returns layer geometry type, feature count, bounding extent, coordinate system, and complete field schema. |
| `export_map` | Exports a map layout frame to high-resolution PNG, JPEG, PDF, or TIFF. |
| `add_layer_to_map` | Adds a spatial dataset (Feature Class, Shapefile, Raster) directly into a project map. |
| `set_basemap` | Changes map basemap to Esri gallery basemaps or custom XYZ tile services (Google, OSM, CartoDB). |
| `set_map_spatial_reference` | Updates the spatial reference / coordinate system (EPSG/WKID) of a project map. |

### 3. Cartography, Symbology & Labeling
| Tool | Description |
|---|---|
| `set_layer_symbology` | Configures layer renderer (`SimpleRenderer`, `UniqueValueRenderer`, `GraduatedColorsRenderer`) with custom colors, sizes, outlines, and break counts. |
| `set_layer_labels` | Toggles dynamic layer labeling with custom Arcade expressions, font sizes, families, and colors. |
| `apply_symbology_from_layer` | Copies symbology and rendering rules from a `.lyrx` layer file or reference layer. |
| `create_layer_file` | Exports a styled layer from an ArcGIS Pro project to a standalone `.lyrx` file. |

### 4. Geoprocessing & Spatial Analysis
| Tool | Description |
|---|---|
| `run_geoprocessing_tool` | Universal runner: dynamically executes **any** ArcPy geoprocessing tool with keyword arguments and captured logs. |
| `buffer_analysis` | Buffers point, line, or polygon features by distance (meters, kilometers, feet) with dissolve options. |
| `clip_analysis` | Clips spatial features using the boundary of another polygon layer. |
| `intersect_analysis` | Computes geometric intersection across multiple feature classes. |
| `spatial_join` | Joins attributes between datasets based on spatial relationships (intersect, within distance, closest, etc.). |
| `dissolve_features` | Aggregates features based on common attribute values and computes summary statistics. |

### 5. Geodatabase & Data Management
| Tool | Description |
|---|---|
| `create_file_gdb` | Creates a new File Geodatabase (`.gdb`) at a specified directory. |
| `create_feature_class` | Creates an empty feature class (Point, Polyline, Polygon) with a specified WKID/EPSG coordinate system. |
| `list_gdb_contents` | Catalogs all feature classes, feature datasets, tables, and rasters inside a geodatabase. |
| `describe_dataset` | Returns detailed schema metadata, shape type, extent, spatial reference, and fields for any dataset. |
| `export_dataset` | Exports/converts datasets between Shapefile, GDB Feature Class, GeoJSON, and CSV. |
| `add_field` | Adds a new column/field (Text, Long, Float, Double, Date) to a table or feature class. |
| `delete_dataset` | Safely removes a feature class, table, or raster dataset. |

### 6. Queries, Selections & Analytical Statistics
| Tool | Description |
|---|---|
| `query_features` | Queries records using SQL `WHERE` clauses with pagination (`limit`/`offset`) and optional Well-Known Text (`WKT`) geometries. |
| `calculate_field` | Computes attribute values using Python 3 expressions or custom function blocks. |
| `select_features_by_attribute` | Filters features with an SQL clause and exports the selection to a new feature class. |
| `select_features_by_location` | Performs spatial selections (contains, within, touches, within distance) and saves the result. |
| `get_summary_statistics` | Calculates statistical aggregates (SUM, MEAN, MIN, MAX, STD) grouped by case fields. |

### 7. Raster & Surface Analysis
| Tool | Description |
|---|---|
| `describe_raster` | Retrieves band count, cell dimensions, pixel type, extent, and statistical distributions for a raster. |
| `create_hillshade` | Generates a 3D shaded relief hillshade raster from an elevation DEM. |
| `calculate_slope` | Calculates terrain slope in degrees or percent rise from an elevation raster. |
| `calculate_aspect` | Computes terrain aspect (downhill slope facing direction) from a DEM. |
| `create_contours` | Generates contour line vector features from an elevation raster. |
| `extract_raster_by_mask` | Clips/extracts raster pixels matching a polygon or raster mask. |

### 8. Custom ArcPy Scripting Execution
| Tool | Description |
|---|---|
| `execute_arcpy_code` | Executes an arbitrary block of Python/ArcPy code in a sandboxed context, returning `stdout`, `stderr`, diagnostic messages, and requested output variable values. |

---

## 🔄 Live Synchronization with Open ArcGIS Pro (`MCP_Sync.pyt`)

When working with an open ArcGIS Pro session, `.aprx` files are locked by the Pro process. 
The MCP Server emits:
1. `active_basemap_state.json`
2. `Active_Basemap.lyrx` (or custom `.lyrx` files)

Using **`toolbox/MCP_Sync.pyt`**, you can update your map live from within ArcGIS Pro with zero application restarts:
1. In ArcGIS Pro **Catalog Pane** -> right-click **Toolboxes** -> **Add Toolbox** -> select `toolbox/MCP_Sync.pyt`.
2. Run **Sync Basemap and Coordinate System** or **Sync All MCP Changes**.
3. (Optional) Right-click the tool and click **Add to Quick Access Toolbar** for single-click instant sync!

See [`toolbox/README_TOOLBOX.md`](toolbox/README_TOOLBOX.md) for full details.
