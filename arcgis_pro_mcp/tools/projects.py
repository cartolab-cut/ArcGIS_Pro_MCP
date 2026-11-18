"""ArcGIS Pro Project (.aprx) and Map management tools using arcpy.mp."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..models import (
    AddLayerToMapRequest,
    ExportMapRequest,
    GetLayerPropertiesRequest,
    InspectProjectRequest,
    ListMapLayersRequest,
    SetBasemapRequest,
    SetSpatialReferenceRequest,
)
from ..services.project_service import ProjectService
from ..utils import arcpy_safe


@arcpy_safe
def inspect_project(project_path: str) -> Dict[str, Any]:
    """Inspects an ArcGIS Pro project (.aprx) file and returns its maps, layouts, and databases.

    Parameters:
        project_path: Absolute or relative path to the .aprx project file.
    """
    req = InspectProjectRequest(project_path=project_path)
    return ProjectService.inspect_project(req.project_path)


@arcpy_safe
def list_map_layers(
    project_path: str,
    map_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Lists all layers and tables within a project's map.

    Parameters:
        project_path: Path to the .aprx project file.
        map_name: Name of the map to inspect. If omitted, the first map in the project is used.
    """
    req = ListMapLayersRequest(project_path=project_path, map_name=map_name)
    return ProjectService.list_map_layers(req.project_path, req.map_name)


@arcpy_safe
def get_layer_properties(
    project_path: str,
    map_name: str,
    layer_name: str,
) -> Dict[str, Any]:
    """Retrieves detailed properties, fields schema, extent, and feature count for a specific layer.

    Parameters:
        project_path: Path to the .aprx project file.
        map_name: Name of the map containing the layer.
        layer_name: Name of the target layer.
    """
    req = GetLayerPropertiesRequest(
        project_path=project_path,
        map_name=map_name,
        layer_name=layer_name,
    )
    return ProjectService.get_layer_properties(
        req.project_path,
        req.map_name,
        req.layer_name,
    )


@arcpy_safe
def export_map(
    project_path: str,
    map_name: str,
    output_image_path: str,
    width: int = 1920,
    height: int = 1080,
    resolution_dpi: int = 300,
    format_type: str = "PNG",
) -> Dict[str, Any]:
    """Exports a project map view directly to an image or document (PNG, JPEG, PDF, etc.).

    Parameters:
        project_path: Path to the .aprx project file.
        map_name: Name of the map to export.
        output_image_path: Destination path for the exported image/document.
        width: Output image width in pixels.
        height: Output image height in pixels.
        resolution_dpi: Image resolution DPI (dots per inch).
        format_type: Format ('PNG', 'JPEG', 'PDF', 'TIFF').
    """
    req = ExportMapRequest(
        project_path=project_path,
        map_name=map_name,
        output_image_path=output_image_path,
        width=width,
        height=height,
        resolution_dpi=resolution_dpi,
        format_type=format_type,
    )
    return ProjectService.export_map(
        project_path=req.project_path,
        map_name=req.map_name,
        output_image_path=req.output_image_path,
        width=req.width,
        height=req.height,
        resolution_dpi=req.resolution_dpi,
        format_type=req.format_type,
    )


@arcpy_safe
def add_layer_to_map(
    project_path: str,
    map_name: str,
    data_path: str,
    save_copy_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Adds a spatial dataset (Feature Class, Shapefile, Raster) into a project map.

    Parameters:
        project_path: Path to the .aprx project file.
        map_name: Name of the map.
        data_path: Path to the feature class, shapefile, or raster to add.
        save_copy_path: Optional path to save a copy of the modified .aprx. If None, overwrites project.
    """
    req = AddLayerToMapRequest(
        project_path=project_path,
        map_name=map_name,
        data_path=data_path,
        save_copy_path=save_copy_path,
    )
    return ProjectService.add_layer_to_map(
        project_path=req.project_path,
        map_name=req.map_name,
        data_path=req.data_path,
        save_copy_path=req.save_copy_path,
    )


@arcpy_safe
def set_basemap(
    project_path: str,
    basemap_name: str,
    map_name: Optional[str] = None,
    custom_url: Optional[str] = None,
    save_copy_path: Optional[str] = None,
    export_lyrx: bool = False,
) -> Dict[str, Any]:
    """Changes the basemap of a project map to a built-in gallery basemap or custom XYZ tile service.

    Parameters:
        project_path: Path to the .aprx project file.
        basemap_name: Name of the basemap (e.g. 'Google Satellite', 'Topographic', 'Imagery', 'OpenStreetMap').
        map_name: Optional name of the map. If None, the first map in the project is used.
        custom_url: Optional custom XYZ tile service URL template (e.g. 'https://.../{level}/{col}/{row}.png').
        save_copy_path: Optional path to save a copy of the modified .aprx.
        export_lyrx: Whether to export an 'Active_Basemap.lyrx' in the project folder (default: False).
    """
    req = SetBasemapRequest(
        project_path=project_path,
        basemap_name=basemap_name,
        map_name=map_name,
        custom_url=custom_url,
        save_copy_path=save_copy_path,
        export_lyrx=export_lyrx,
    )
    return ProjectService.set_basemap(
        project_path=req.project_path,
        basemap_name=req.basemap_name,
        map_name=req.map_name,
        custom_url=req.custom_url,
        save_copy_path=req.save_copy_path,
        export_lyrx=req.export_lyrx,
    )


@arcpy_safe
def set_map_spatial_reference(
    project_path: str,
    epsg_code: int,
    map_name: Optional[str] = None,
    save_copy_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Sets the spatial reference (coordinate system / EPSG) of a project map.

    Parameters:
        project_path: Path to the .aprx project file.
        epsg_code: EPSG or factory code (e.g. 6312 for Cyprus CGRS93, 4326 for WGS84, 3857 for Web Mercator).
        map_name: Optional name of the map. If None, the first map in the project is used.
        save_copy_path: Optional path to save a copy of the modified .aprx.
    """
    req = SetSpatialReferenceRequest(
        project_path=project_path,
        epsg_code=epsg_code,
        map_name=map_name,
        save_copy_path=save_copy_path,
    )
    return ProjectService.set_map_spatial_reference(
        project_path=req.project_path,
        epsg_code=req.epsg_code,
        map_name=req.map_name,
        save_copy_path=req.save_copy_path,
    )
