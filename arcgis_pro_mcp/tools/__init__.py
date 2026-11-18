"""Tool exports for ArcGIS Pro MCP Server."""

from .system import (
    get_arcgis_system_info,
    set_arcgis_environment,
    manage_extension,
)
from .projects import (
    inspect_project,
    list_map_layers,
    get_layer_properties,
    export_map,
    add_layer_to_map,
    set_basemap,
    set_map_spatial_reference,
)
from .cartography import (
    set_layer_symbology,
    set_layer_labels,
    apply_symbology_from_layer,
    create_layer_file,
)
from .geoprocessing import (
    run_geoprocessing_tool,
    buffer_analysis,
    clip_analysis,
    intersect_analysis,
    spatial_join,
    dissolve_features,
)
from .data_management import (
    create_file_gdb,
    create_feature_class,
    list_gdb_contents,
    describe_dataset,
    export_dataset,
    add_field,
    delete_dataset,
)
from .analysis import (
    query_features,
    calculate_field,
    select_features_by_attribute,
    select_features_by_location,
    get_summary_statistics,
)
from .raster import (
    describe_raster,
    create_hillshade,
    calculate_slope,
    calculate_aspect,
    create_contours,
    extract_raster_by_mask,
)
from .scripting import (
    execute_arcpy_code,
)

__all__ = [
    # System
    "get_arcgis_system_info",
    "set_arcgis_environment",
    "manage_extension",
    # Projects
    "inspect_project",
    "list_map_layers",
    "get_layer_properties",
    "export_map",
    "add_layer_to_map",
    "set_basemap",
    "set_map_spatial_reference",
    # Cartography & Symbology
    "set_layer_symbology",
    "set_layer_labels",
    "apply_symbology_from_layer",
    "create_layer_file",
    # Geoprocessing
    "run_geoprocessing_tool",
    "buffer_analysis",
    "clip_analysis",
    "intersect_analysis",
    "spatial_join",
    "dissolve_features",
    # Data Management
    "create_file_gdb",
    "create_feature_class",
    "list_gdb_contents",
    "describe_dataset",
    "export_dataset",
    "add_field",
    "delete_dataset",
    # Analysis & Query
    "query_features",
    "calculate_field",
    "select_features_by_attribute",
    "select_features_by_location",
    "get_summary_statistics",
    # Raster
    "describe_raster",
    "create_hillshade",
    "calculate_slope",
    "calculate_aspect",
    "create_contours",
    "extract_raster_by_mask",
    # Scripting
    "execute_arcpy_code",
]
