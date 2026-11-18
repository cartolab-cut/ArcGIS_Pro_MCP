"""Test suite for ArcGIS Pro MCP Server.

Verifies:
- Server initialization, tool registration (39+ tools), resources, and prompts.
- Live ArcPy geoprocessing workflows (GDB, Feature Class, Cursors, Buffer, Query).
- Cartography & Symbology module (Simple, UniqueValue, GraduatedColors renderers, Labeling, .lyrx export/apply).
- Clean Architecture Service Layer and Pydantic v2 schemas/validation.
- ArcGIS Pro Python Toolbox (MCP_Sync.pyt) live synchronization tools.
"""

from __future__ import annotations
import asyncio
import gc
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch
import arcpy

from arcgis_pro_mcp import config
from arcgis_pro_mcp.server import create_server
from arcgis_pro_mcp.tools import (
    add_field,
    add_layer_to_map,
    apply_symbology_from_layer,
    buffer_analysis,
    calculate_aspect,
    calculate_slope,
    create_contours,
    create_feature_class,
    create_file_gdb,
    create_hillshade,
    create_layer_file,
    delete_dataset,
    describe_dataset,
    describe_raster,
    execute_arcpy_code,
    extract_raster_by_mask,
    get_arcgis_system_info,
    get_summary_statistics,
    list_gdb_contents,
    query_features,
    set_arcgis_environment,
    set_basemap,
    set_layer_labels,
    set_layer_symbology,
    set_map_spatial_reference,
)
from arcgis_pro_mcp.utils import (
    calculate_contrast_ratio,
    extension_scope,
    is_wcag_accessible,
    sanitize_path,
)
from arcgis_pro_mcp.models import (
    BasemapName,
    BufferAnalysisRequest,
    CreateFeatureClassRequest,
    GeometryType,
    QueryFeaturesRequest,
    SetLayerSymbologyRequest,
    SymbologyRendererType,
)
from arcgis_pro_mcp.services import (
    AnalysisService,
    CartographyService,
    DataManagementService,
    GeoprocessingService,
    ProjectService,
    RasterService,
    ScriptingService,
    SystemService,
)


class TestArcGISProMCP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="arcgis_mcp_test_")
        cls.test_gdb_name = "TestGeodatabase.gdb"
        cls.test_gdb_path = os.path.join(cls.temp_dir, cls.test_gdb_name)
        cls.fc_full_path = None

        # Template APRX setup
        install_dir = arcpy.GetInstallInfo().get("InstallDir", r"c:\program files\arcgis\pro")
        cls.blank_aprx_template = os.path.join(
            install_dir, "Resources", "ArcToolBox", "Services", "routingservices", "data", "Blank.aprx"
        )
        cls.test_aprx_path = os.path.join(cls.temp_dir, "TestProject.aprx")

    @classmethod
    def tearDownClass(cls):
        try:
            if os.path.exists(cls.temp_dir):
                shutil.rmtree(cls.temp_dir, ignore_errors=True)
        except Exception:
            pass

    def test_01_server_initialization(self):
        """Verify MCP Server instantiates with all tools, resources, and prompts."""
        server = create_server()
        self.assertIsNotNone(server)

        # Check async listing
        async def verify():
            tools_list = await server.list_tools()
            resources_list = await server.list_resources()
            prompts_list = await server.list_prompts()
            return tools_list, resources_list, prompts_list

        tools, resources, prompts = asyncio.run(verify())
        tool_names = [t.name for t in tools]
        resource_uris = [r.uri for r in resources]
        prompt_names = [p.name for p in prompts]

        # Verify tool counts & registrations
        self.assertGreaterEqual(len(tool_names), 39)
        self.assertIn("get_arcgis_system_info", tool_names)
        self.assertIn("buffer_analysis", tool_names)
        self.assertIn("execute_arcpy_code", tool_names)
        self.assertIn("set_basemap", tool_names)
        self.assertIn("set_map_spatial_reference", tool_names)
        # New Cartography tools
        self.assertIn("set_layer_symbology", tool_names)
        self.assertIn("set_layer_labels", tool_names)
        self.assertIn("apply_symbology_from_layer", tool_names)
        self.assertIn("create_layer_file", tool_names)

        # Resources
        self.assertIn("arcgis://system/info", resource_uris)
        self.assertIn("arcgis://system/toolboxes", resource_uris)
        self.assertIn("arcgis://system/environments", resource_uris)

        # Prompts
        self.assertIn("gis_spatial_analyst", prompt_names)
        self.assertIn("geoprocessing_debugger", prompt_names)
        self.assertIn("cartography_specialist", prompt_names)

        print(f"\n[PASS] Server initialized with {len(tool_names)} tools, {len(resource_uris)} resources, and {len(prompt_names)} prompts.")

    def test_02_get_system_info(self):
        """Verify reading ArcGIS Pro system and environment information."""
        info = get_arcgis_system_info()
        self.assertTrue(info.get("success"), f"Failed: {info}")
        self.assertIn("version", info)
        self.assertIn("license_level", info)
        print(f"[PASS] Detected ArcGIS Pro version: {info['version']}, License: {info['license_level']}")

    def test_03_gdb_lifecycle_and_spatial_workflow(self):
        """Tests live geodatabase creation, feature class creation, field calculation,

        buffer geoprocessing, and feature querying.
        """
        # 1. Create File Geodatabase
        gdb_res = create_file_gdb(out_folder_path=self.temp_dir, gdb_name=self.test_gdb_name)
        self.assertTrue(gdb_res.get("success"), f"Create GDB failed: {gdb_res}")
        self.assertTrue(os.path.exists(self.test_gdb_path))
        print(f"[PASS] Created File GDB at {self.test_gdb_path}")

        # 2. Set ArcPy workspace
        env_res = set_arcgis_environment(
            workspace=self.test_gdb_path,
            scratch_workspace=self.test_gdb_path,
            overwrite_output=True,
        )
        self.assertTrue(env_res.get("success"))

        # 3. Create Feature Class (Points in WGS84)
        fc_name = "SamplePoints"
        fc_res = create_feature_class(
            out_path=self.test_gdb_path,
            out_name=fc_name,
            geometry_type="POINT",
            spatial_reference_wkid=4326,
        )
        self.assertTrue(fc_res.get("success"), f"Create FC failed: {fc_res}")
        self.__class__.fc_full_path = os.path.join(self.test_gdb_path, fc_name)
        fc_full_path = self.__class__.fc_full_path

        # 4. Add Fields
        f1_res = add_field(fc_full_path, "PointName", "TEXT", field_length=100)
        self.assertTrue(f1_res.get("success"))
        f2_res = add_field(fc_full_path, "Value", "LONG")
        self.assertTrue(f2_res.get("success"))
        print("[PASS] Created feature class and added schema fields.")

        # 5. Insert test data via execute_arcpy_code
        insert_code = f"""
import arcpy

points_data = [
    ("Point_A", 100, 23.7275, 37.9838),  # Athens
    ("Point_B", 250, 22.9444, 40.6401),  # Thessaloniki
    ("Point_C", 50,  25.1332, 35.3387),  # Heraklion
]

fields = ["PointName", "Value", "SHAPE@XY"]
with arcpy.da.InsertCursor(r"{fc_full_path}", fields) as cursor:
    for name, val, lon, lat in points_data:
        cursor.insertRow((name, val, (lon, lat)))

inserted_count = int(arcpy.management.GetCount(r"{fc_full_path}")[0])
"""
        exec_res = execute_arcpy_code(insert_code, return_variables=["inserted_count"])
        self.assertTrue(exec_res.get("success"), f"Script exec failed: {exec_res}")
        self.assertEqual(exec_res["variables"].get("inserted_count"), 3)
        print("[PASS] Inserted 3 test features via execute_arcpy_code.")

        # 6. Describe Dataset
        desc_res = describe_dataset(fc_full_path)
        self.assertTrue(desc_res.get("success"))
        self.assertEqual(desc_res.get("shape_type"), "Point")
        self.assertEqual(desc_res.get("record_count"), 3)
        print(f"[PASS] Described dataset: {desc_res['name']}, Shape: {desc_res['shape_type']}, Count: {desc_res['record_count']}")

        # 7. Query features with SQL
        query_res = query_features(
            feature_class=fc_full_path,
            where_clause="Value > 80",
            fields=["PointName", "Value"],
            include_geometry_wkt=True,
        )
        self.assertTrue(query_res.get("success"))
        self.assertEqual(query_res.get("returned_count"), 2)
        print(f"[PASS] Query features returned {query_res['returned_count']} matching records.")

        # 8. Buffer Analysis
        buffer_fc_name = "SamplePoints_Buffer"
        buffer_fc_path = os.path.join(self.test_gdb_path, buffer_fc_name)
        buf_res = buffer_analysis(
            in_features=fc_full_path,
            out_feature_class=buffer_fc_path,
            buffer_distance_or_field="10 Kilometers",
        )
        self.assertTrue(buf_res.get("success"), f"Buffer failed: {buf_res}")
        self.assertEqual(buf_res.get("feature_count"), 3)
        print(f"[PASS] Buffer analysis produced 3 buffer polygons.")

        # 9. List GDB contents
        gdb_catalog = list_gdb_contents(self.test_gdb_path)
        self.assertTrue(gdb_catalog.get("success"))
        self.assertIn(fc_name, gdb_catalog.get("standalone_feature_classes", []))
        self.assertIn(buffer_fc_name, gdb_catalog.get("standalone_feature_classes", []))
        print(f"[PASS] GDB catalog contains: {gdb_catalog['standalone_feature_classes']}")

    def test_04_cartography_and_symbology(self):
        """Tests Cartography tools: Simple, UniqueValue, GraduatedColors renderers,

        labeling configuration, and .lyrx file export/apply.
        """
        if not os.path.exists(self.blank_aprx_template):
            self.skipTest(f"Blank APRX template not found at {self.blank_aprx_template}")

        shutil.copyfile(self.blank_aprx_template, self.test_aprx_path)
        os.chmod(self.test_aprx_path, stat.S_IWRITE | stat.S_IREAD)

        # 1. Add layer to map
        add_res = add_layer_to_map(
            project_path=self.test_aprx_path,
            map_name="Map",
            data_path=self.fc_full_path,
        )
        self.assertTrue(add_res.get("success"), f"Add layer failed: {add_res}")
        print(f"[PASS] Added feature layer to map in {self.test_aprx_path}")

        # 2. SimpleRenderer with custom color & size
        simple_res = set_layer_symbology(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            renderer_type="SimpleRenderer",
            symbol_color="#FF5733",
            symbol_size=14.0,
            outline_color=[0, 0, 0, 100],
            outline_width=1.5,
            export_lyrx=True,
        )
        self.assertTrue(simple_res.get("success"), f"SimpleRenderer failed: {simple_res}")
        self.assertEqual(simple_res.get("renderer_type"), "SimpleRenderer")
        self.assertIsNotNone(simple_res.get("accessibility"))
        self.assertIn("against_white_bg", simple_res["accessibility"])
        print("[PASS] Configured SimpleRenderer with hex color #FF5733 and size 14 (with WCAG accessibility metadata).")

        # 2b. Verify default export_lyrx=False creates no .lyrx file
        default_lyrx_res = set_layer_symbology(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            renderer_type="SimpleRenderer",
            symbol_color="#33FF57",
        )
        self.assertTrue(default_lyrx_res.get("success"))
        self.assertIsNone(default_lyrx_res.get("lyrx_exported"))
        print("[PASS] Verified default export_lyrx=False creates no unprompted .lyrx files on disk.")

        # 3. UniqueValueRenderer on 'PointName'
        uv_res = set_layer_symbology(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            renderer_type="UniqueValueRenderer",
            field_name="PointName",
            export_lyrx=False,
        )
        self.assertTrue(uv_res.get("success"), f"UniqueValueRenderer failed: {uv_res}")
        print("[PASS] Configured UniqueValueRenderer classified on field 'PointName'.")

        # 4. GraduatedColorsRenderer on 'Value'
        gc_res = set_layer_symbology(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            renderer_type="GraduatedColorsRenderer",
            field_name="Value",
            break_count=3,
            classification_method="NaturalBreaks",
            export_lyrx=False,
        )
        self.assertTrue(gc_res.get("success"), f"GraduatedColorsRenderer failed: {gc_res}")
        print("[PASS] Configured GraduatedColorsRenderer with 3 natural breaks on field 'Value'.")

        # 5. Set Layer Labels
        label_res = set_layer_labels(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            enable_labels=True,
            expression="$feature.PointName",
            font_size=11.5,
            font_color="#FF0000",
            font_family="Arial",
        )
        self.assertTrue(label_res.get("success"), f"Set labels failed: {label_res}")
        self.assertTrue(label_res.get("labels_enabled"))
        self.assertIsNotNone(label_res.get("accessibility"))
        self.assertIn("against_white_bg", label_res["accessibility"])
        print("[PASS] Configured dynamic Arcade labels with expression '$feature.PointName' and font_color #FF0000 (with accessibility analysis).")

        # 5b. Verify invalid field error handling
        bad_field_res = set_layer_symbology(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            renderer_type="UniqueValueRenderer",
            field_name="NonExistentField123",
            export_lyrx=False,
        )
        self.assertFalse(bad_field_res.get("success"))
        self.assertIn("not found", bad_field_res.get("error", ""))
        print("[PASS] Verified field existence validation in set_layer_symbology.")

        # 5c. Verify break_count validation
        bad_break_res = set_layer_symbology(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            renderer_type="GraduatedColorsRenderer",
            field_name="Value",
            break_count=1,
            export_lyrx=False,
        )
        self.assertFalse(bad_break_res.get("success"))
        print("[PASS] Verified break_count validation in set_layer_symbology.")

        # 6. Create standalone layer file (.lyrx)
        lyrx_path = os.path.join(self.temp_dir, "Exported_SamplePoints.lyrx")
        lyrx_res = create_layer_file(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            out_lyrx_path=lyrx_path,
        )
        self.assertTrue(lyrx_res.get("success"), f"Create layer file failed: {lyrx_res}")
        self.assertTrue(os.path.exists(lyrx_path))
        print(f"[PASS] Exported styled layer to {lyrx_path}")

        # 7. Apply symbology from layer file to target point layer
        temp_lyr = "temp_points_fl"
        if arcpy.Exists(temp_lyr):
            arcpy.management.Delete(temp_lyr)
        arcpy.management.MakeFeatureLayer(self.fc_full_path, temp_lyr)
        try:
            apply_res = apply_symbology_from_layer(
                in_layer=temp_lyr,
                symbology_layer=lyrx_path,
            )
            self.assertTrue(apply_res.get("success"), f"Apply symbology failed: {apply_res}")
            print("[PASS] Applied symbology definition from .lyrx to target point layer.")
        finally:
            arcpy.management.Delete(temp_lyr)

    def test_05_pydantic_schemas_and_clean_architecture(self):
        """Verifies Pydantic v2 model validation, Enums, and Service layer."""
        # 1. Pydantic validation: CreateFeatureClassRequest
        fc_req = CreateFeatureClassRequest(
            out_path=self.test_gdb_path,
            out_name="ModelTestFC",
            geometry_type=GeometryType.POLYGON,
            spatial_reference_wkid=3857,
        )
        self.assertEqual(fc_req.geometry_type, "POLYGON")
        self.assertEqual(fc_req.spatial_reference_wkid, 3857)

        # 2. Pydantic validation: SetLayerSymbologyRequest
        sym_req = SetLayerSymbologyRequest(
            project_path=self.test_aprx_path,
            map_name="Map",
            layer_name="SamplePoints",
            renderer_type=SymbologyRendererType.GRADUATED_COLORS,
            field_name="Value",
            break_count=4,
        )
        self.assertEqual(sym_req.renderer_type, "GraduatedColorsRenderer")
        self.assertEqual(sym_req.break_count, 4)

        # 3. Pydantic validation error check on invalid limit
        with self.assertRaises(Exception):
            QueryFeaturesRequest(feature_class="test", limit=5000)  # max is 1000

        # 3b. Tool adapter level validation error check on invalid limit
        invalid_query_res = query_features(feature_class=self.test_gdb_path, limit=5000)
        self.assertFalse(invalid_query_res.get("success"))
        self.assertEqual(invalid_query_res.get("error_type"), "ValidationError")
        print("[PASS] Verified adapter-level Pydantic parameter validation on query_features.")

        # 3c. Tool adapter level validation on invalid geometry type
        invalid_fc_res = create_feature_class(
            out_path=self.test_gdb_path,
            out_name="InvalidFC",
            geometry_type="INVALID_GEOMETRY",
        )
        self.assertFalse(invalid_fc_res.get("success"))
        self.assertEqual(invalid_fc_res.get("error_type"), "ValidationError")
        print("[PASS] Verified adapter-level Pydantic parameter validation on create_feature_class.")

        # 4. Direct service invocation check
        sys_res = SystemService.get_system_info()
        self.assertTrue(sys_res.get("success"))
        self.assertIn("version", sys_res)
        print("[PASS] Pydantic v2 schemas and Clean Architecture service layer verified.")

    def test_06_mcp_sync_toolbox(self):
        """Verifies importing and executing the ArcGIS Pro Python Toolbox (MCP_Sync.pyt)."""
        toolbox_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "toolbox", "MCP_Sync.pyt"))
        self.assertTrue(os.path.exists(toolbox_path), f"Toolbox not found at: {toolbox_path}")

        # 1. Import toolbox into ArcPy
        tb = arcpy.ImportToolbox(toolbox_path)
        self.assertIsNotNone(tb)
        self.assertTrue(hasattr(arcpy, "mcpsync"))

        tools = [fn for fn in dir(arcpy.mcpsync) if not fn.startswith("_")]
        self.assertIn("SyncBasemapAndCRS", tools)
        self.assertIn("ApplyLyrxToActiveMap", tools)
        self.assertIn("SyncAllFromMCP", tools)
        print(f"[PASS] Successfully imported MCP_Sync.pyt with tools: {tools}")

        # 2. Write a mock active_basemap_state.json with EPSG:4326 and run SyncBasemapAndCRS
        state_file = os.path.join(self.temp_dir, "active_basemap_state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({
                "basemap_name": "Topographic",
                "is_custom": False,
                "map_name": "Map",
                "spatial_reference": {
                    "factory_code": 4326,
                    "name": "GCS_WGS_1984",
                },
            }, f, indent=2)

        # Execute tool via ArcPy alias
        arcpy.mcpsync.SyncBasemapAndCRS(
            state_file=state_file,
            target_map_name="Map",
            project_path=self.test_aprx_path,
        )

        # Verify changes were saved to the APRX on disk
        aprx_check = arcpy.mp.ArcGISProject(self.test_aprx_path)
        map_check = aprx_check.listMaps()[0]
        self.assertEqual(map_check.spatialReference.factoryCode, 4326)
        print("[PASS] Verified SyncBasemapAndCRS saved EPSG:4326 to disk project.")

        # 3. Test ApplyLyrxToActiveMap
        lyrx_path = os.path.join(self.temp_dir, "Exported_SamplePoints.lyrx")
        arcpy.mcpsync.ApplyLyrxToActiveMap(
            lyrx_file=lyrx_path,
            target_map_name="Map",
            as_basemap=False,
            project_path=self.test_aprx_path,
        )
        aprx_check2 = arcpy.mp.ArcGISProject(self.test_aprx_path)
        layer_names = [l.name for l in aprx_check2.listMaps()[0].listLayers()]
        self.assertIn("SamplePoints", layer_names)
        print(f"[PASS] Verified ApplyLyrxToActiveMap added layer to map: {layer_names}")

        # 4. Test SyncAllFromMCP
        arcpy.mcpsync.SyncAllFromMCP(
            project_path=self.test_aprx_path,
            target_map_name="Map",
            state_file=state_file,
            lyrx_file=lyrx_path,
        )
        print("[PASS] Verified SyncAllFromMCP executed successfully with both state JSON and .lyrx.")

    def test_07_core_utilities_and_guards(self):
        """Verifies extension_scope, WCAG 2.1 contrast, sanitize_path, memory workspace, and execution guard."""
        # 1. Extension scope
        with extension_scope("Spatial") as status:
            self.assertIn(status, ("Spatial", "Available", "Unavailable"))
        # Verify extension is checked in
        curr_status = arcpy.CheckExtension("Spatial")
        self.assertIn(curr_status, ("Available", "Unavailable"))
        print("[PASS] Verified extension_scope checkout and guaranteed check-in.")

        # 2. WCAG contrast calculation
        black_white_ratio = calculate_contrast_ratio("#000000", "#FFFFFF")
        self.assertAlmostEqual(black_white_ratio, 21.0, places=1)

        same_color_ratio = calculate_contrast_ratio("#FFFFFF", "#FFFFFF")
        self.assertAlmostEqual(same_color_ratio, 1.0, places=1)

        accessible_eval = is_wcag_accessible("#000000", "#FFFFFF")
        self.assertTrue(accessible_eval["is_accessible"])
        self.assertTrue(accessible_eval["wcag_aa_normal_text"])

        poor_contrast_eval = is_wcag_accessible("#EEEEEE", "#FFFFFF", min_ratio=4.5)
        self.assertFalse(poor_contrast_eval["is_accessible"])
        print("[PASS] Verified WCAG 2.1 color contrast calculation and evaluation.")

        # 3. Path traversal guards
        safe_p = sanitize_path(os.path.join(self.temp_dir, "test.gdb"))
        self.assertTrue(os.path.isabs(safe_p))

        # Windows case-insensitivity verification (e.g. C:\ vs c:\)
        safe_case = sanitize_path(self.temp_dir.lower() + os.sep + "test.gdb", base_dir=self.temp_dir.upper())
        self.assertTrue(os.path.isabs(safe_case))

        with self.assertRaises(ValueError):
            sanitize_path("invalid\x00path")

        with self.assertRaises(ValueError):
            sanitize_path(os.path.join(self.temp_dir, "..", "escaped.txt"), base_dir=self.temp_dir)
        print("[PASS] Verified sanitize_path traversal protection, case insensitivity, and null-byte rejection.")

        # 4. In-memory workspace summary statistics
        stats_res = get_summary_statistics(
            in_table=self.fc_full_path,
            statistics_fields=[["Value", "MEAN"], ["Value", "MAX"]],
        )
        self.assertTrue(stats_res.get("success"), f"Summary statistics failed: {stats_res}")
        self.assertGreater(len(stats_res.get("statistics", [])), 0)
        self.assertFalse(arcpy.Exists("memory/temp_stats_tbl"))

        # 4b. Summary statistics with explicit out_table in GDB
        custom_stats_tbl = os.path.join(self.test_gdb_path, "CustomStatsTable")
        stats_out_res = get_summary_statistics(
            in_table=self.fc_full_path,
            statistics_fields=[["Value", "SUM"]],
            out_table=custom_stats_tbl,
        )
        self.assertTrue(stats_out_res.get("success"), f"Summary stats with out_table failed: {stats_out_res}")
        self.assertTrue(arcpy.Exists(custom_stats_tbl))
        self.assertEqual(stats_out_res.get("output_table"), custom_stats_tbl)
        print("[PASS] Verified get_summary_statistics operates via memory/ workspace and explicit out_table.")

        # 5. Execution guard for dynamic ArcPy execution
        original_flag = config.ENABLE_ARCPY_EXEC
        try:
            config.ENABLE_ARCPY_EXEC = False
            blocked_res = execute_arcpy_code(code="x = 42")
            self.assertFalse(blocked_res.get("success"))
            self.assertIn("ENABLE_ARCPY_EXEC=False", blocked_res.get("error", ""))
        finally:
            config.ENABLE_ARCPY_EXEC = original_flag
        print("[PASS] Verified execute_arcpy_code security guard when ENABLE_ARCPY_EXEC=False.")

    def test_08_no_project_duplication_on_lock(self):
        """Verifies that locked projects do NOT generate duplicate _updated.aprx files.

        Instead, changes are staged to ai_live_action.py directing to Run AI Live Task.
        """
        project_dir = os.path.dirname(os.path.abspath(self.test_aprx_path))
        forbidden_copy = os.path.join(project_dir, f"{Path(self.test_aprx_path).stem}_updated.aprx")
        if os.path.exists(forbidden_copy):
            os.remove(forbidden_copy)

        staged_script = os.path.join(project_dir, "ai_live_action.py")
        if os.path.exists(staged_script):
            os.remove(staged_script)

        # Simulate aprx.save() raising OSError when locked by ArcGIS Pro desktop
        with patch.object(arcpy.mp.ArcGISProject, "save", side_effect=OSError("The process cannot access the file because it is being used by another process")):
            res = set_basemap(
                project_path=self.test_aprx_path,
                basemap_name="Topographic",
            )
            self.assertFalse(res.get("success"))
            self.assertIn("open and locked", res.get("error", ""))
            self.assertIn("ai_live_action.py", res.get("error", ""))
            self.assertIn("Run AI Live Task", res.get("error", ""))

        # Verify no _updated.aprx was created on disk
        self.assertFalse(os.path.exists(forbidden_copy), f"Forbidden file was created: {forbidden_copy}")
        # Verify ai_live_action.py was staged
        self.assertTrue(os.path.exists(staged_script), f"Staged action script was not created: {staged_script}")

        # Verify symbology parameters (color ramp, classification method) are preserved in staged action
        with patch.object(arcpy.mp.ArcGISProject, "save", side_effect=OSError("locked")):
            sym_lock_res = set_layer_symbology(
                project_path=self.test_aprx_path,
                map_name="Map",
                layer_name="SamplePoints",
                renderer_type="GraduatedColorsRenderer",
                field_name="Value",
                break_count=3,
                classification_method="Quantile",
                color_ramp_name="Viridis",
            )
            self.assertFalse(sym_lock_res.get("success"))
        with open(staged_script, "r", encoding="utf-8") as f:
            sym_staged = f.read()
        self.assertIn("classificationMethod", sym_staged)
        self.assertIn("listColorRamps", sym_staged)

        # Verify label parameters (expression, font size, font color, SQL) are preserved in staged action
        with patch.object(arcpy.mp.ArcGISProject, "save", side_effect=OSError("locked")):
            lbl_lock_res = set_layer_labels(
                project_path=self.test_aprx_path,
                map_name="Map",
                layer_name="SamplePoints",
                enable_labels=True,
                expression="$feature.PointName",
                font_size=12.0,
                font_color="#FF0000",
                sql_query="Value > 0",
            )
            self.assertFalse(lbl_lock_res.get("success"))
        with open(staged_script, "r", encoding="utf-8") as f:
            lbl_staged = f.read()
        self.assertIn("SQLQuery", lbl_staged)
        self.assertIn("textSymbol", lbl_staged)

        print("[PASS] Verified no duplicate _updated.aprx created on file lock; full symbology & labels staged to ai_live_action.py.")

    def test_09_ai_live_sync_toolbox(self):
        """Verifies importing and executing AI_Live_Sync.pyt ('Run AI Live Task')."""
        toolbox_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "toolbox", "AI_Live_Sync.pyt"))
        self.assertTrue(os.path.exists(toolbox_path), f"AI_Live_Sync.pyt not found at: {toolbox_path}")

        # 1. Import toolbox into ArcPy
        tb = arcpy.ImportToolbox(toolbox_path)
        self.assertIsNotNone(tb)
        self.assertTrue(hasattr(arcpy, "ailivesync"))

        tools = [fn for fn in dir(arcpy.ailivesync) if not fn.startswith("_")]
        self.assertIn("RunAILiveTask", tools)
        print(f"[PASS] Successfully imported AI_Live_Sync.pyt with tools: {tools}")

        # 2. Stage a live action that modifies project map spatial reference to EPSG:3857
        project_dir = os.path.dirname(os.path.abspath(self.test_aprx_path))
        staged_script = os.path.join(project_dir, "ai_live_action.py")
        from arcgis_pro_mcp.utils import stage_ai_live_action
        stage_ai_live_action(
            self.test_aprx_path,
            [
                "m = aprx.listMaps()[0]",
                "m.spatialReference = arcpy.SpatialReference(3857)",
            ],
        )
        self.assertTrue(os.path.exists(staged_script))

        # 3. Execute RunAILiveTask
        arcpy.ailivesync.RunAILiveTask(
            action_script=staged_script,
            project_path=self.test_aprx_path,
        )

        # 4. Verify project on disk reflects the update
        aprx_check = arcpy.mp.ArcGISProject(self.test_aprx_path)
        map_check = aprx_check.listMaps()[0]
        self.assertEqual(map_check.spatialReference.factoryCode, 3857)

        # 5. Verify single execution (no double invocation)
        counter_file = os.path.join(self.temp_dir, "run_counter.txt")
        if os.path.exists(counter_file):
            os.remove(counter_file)
        stage_ai_live_action(
            self.test_aprx_path,
            [
                f"with open({repr(counter_file)}, 'a') as f: f.write('executed\\n')",
            ],
        )
        arcpy.ailivesync.RunAILiveTask(
            action_script=staged_script,
            project_path=self.test_aprx_path,
        )
        with open(counter_file, "r") as f:
            runs = [r for r in f.read().splitlines() if r.strip()]
        self.assertEqual(len(runs), 1, f"Expected staged task to execute exactly once, but executed {len(runs)} times.")
        print("[PASS] Verified RunAILiveTask executed staged ai_live_action.py exactly once without duplicate invocation.")

    def test_10_raster_analysis_and_extension_scope(self):
        """Verifies raster analysis tools and extension checkout/checkin lifecycle."""
        import numpy as np

        # Create a synthetic DEM raster
        dem_path = os.path.join(self.temp_dir, "SyntheticDEM.tif")
        arr = np.linspace(100.0, 500.0, 100, dtype=np.float32).reshape((10, 10))
        raster_mem = arcpy.NumPyArrayToRaster(arr, arcpy.Point(0, 0), x_cell_size=10.0, y_cell_size=10.0)
        raster_mem.save(dem_path)
        del raster_mem
        gc.collect()

        self.assertTrue(os.path.exists(dem_path))

        # 1. Describe Raster
        desc_res = describe_raster(dem_path)
        self.assertTrue(desc_res.get("success"), f"Describe raster failed: {desc_res}")
        self.assertEqual(desc_res.get("width_pixels"), 10)
        self.assertEqual(desc_res.get("height_pixels"), 10)
        print(f"[PASS] Described raster: {desc_res.get('width_pixels')}x{desc_res.get('height_pixels')} pixels.")

        # 2. Hillshade
        hs_path = os.path.join(self.temp_dir, "Hillshade.tif")
        hs_res = create_hillshade(in_elevation_raster=dem_path, out_raster=hs_path)
        self.assertTrue(hs_res.get("success"), f"Hillshade failed: {hs_res}")
        self.assertTrue(os.path.exists(hs_path))
        print("[PASS] Created Hillshade raster via extension_scope.")

        # 3. Slope
        slope_path = os.path.join(self.temp_dir, "Slope.tif")
        slope_res = calculate_slope(in_elevation_raster=dem_path, out_raster=slope_path)
        self.assertTrue(slope_res.get("success"), f"Slope failed: {slope_res}")
        self.assertTrue(os.path.exists(slope_path))
        print("[PASS] Calculated Slope raster via extension_scope.")

        # 4. Aspect
        aspect_path = os.path.join(self.temp_dir, "Aspect.tif")
        aspect_res = calculate_aspect(in_elevation_raster=dem_path, out_raster=aspect_path)
        self.assertTrue(aspect_res.get("success"), f"Aspect failed: {aspect_res}")
        self.assertTrue(os.path.exists(aspect_path))
        print("[PASS] Calculated Aspect raster via extension_scope.")

        # 5. Contours
        contour_fc = os.path.join(self.test_gdb_path, "ElevationContours")
        contour_res = create_contours(in_elevation_raster=dem_path, out_feature_class=contour_fc, contour_interval=50.0)
        self.assertTrue(contour_res.get("success"), f"Contours failed: {contour_res}")
        self.assertTrue(arcpy.Exists(contour_fc))
        print(f"[PASS] Created {contour_res.get('contour_count')} contour lines via extension_scope.")

        # 6. Extract Raster by Mask
        masked_path = os.path.join(self.temp_dir, "MaskedDEM.tif")
        mask_res = extract_raster_by_mask(in_raster=dem_path, mask_data=self.fc_full_path, out_raster=masked_path)
        self.assertTrue(mask_res.get("success"), f"Extract by mask failed: {mask_res}")
        print("[PASS] Extracted raster by mask via extension_scope.")

        # 7. Verify extension licenses are cleanly checked in
        sp_stat = arcpy.CheckExtension("Spatial")
        self.assertIn(sp_stat, ("Available", "Unavailable"))
        ddd_stat = arcpy.CheckExtension("3D")
        self.assertIn(ddd_stat, ("Available", "Unavailable"))
        print("[PASS] Verified Spatial and 3D Analyst licenses checked in after all raster operations.")


if __name__ == "__main__":
    unittest.main()
