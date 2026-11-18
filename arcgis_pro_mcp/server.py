"""Main MCP Server instance and registration for ArcGIS Pro."""

from __future__ import annotations
import argparse
import sys
from typing import Any, Literal
from mcp.server.mcpserver import MCPServer
from . import tools
from .resources import (
    get_available_toolboxes_resource,
    get_environment_settings_resource,
    get_system_info_resource,
)
from .prompts import (
    get_cartography_specialist_prompt,
    get_geoprocessing_debugger_prompt,
    get_spatial_analyst_prompt,
)


def create_server() -> MCPServer:
    """Creates and configures the ArcGIS Pro MCP Server with all tools, resources, and prompts."""
    server = MCPServer(
        name="ArcGIS_Pro_MCP",
        instructions="ArcGIS Pro Model Context Protocol Server providing ArcPy geoprocessing, project inspection, raster analysis, and data management capabilities.",
    )

    # 1. Register all tools
    for tool_name in tools.__all__:
        fn = getattr(tools, tool_name)
        server.add_tool(fn)

    # 2. Register resources
    @server.resource("arcgis://system/info")
    def resource_system_info() -> str:
        """Returns JSON containing ArcGIS Pro version, build, license level, and system status."""
        return get_system_info_resource()

    @server.resource("arcgis://system/toolboxes")
    def resource_toolboxes() -> str:
        """Returns JSON catalog of all available ArcPy geoprocessing toolboxes."""
        return get_available_toolboxes_resource()

    @server.resource("arcgis://system/environments")
    def resource_environments() -> str:
        """Returns JSON state of current geoprocessing environments (arcpy.env)."""
        return get_environment_settings_resource()

    # 3. Register prompts
    @server.prompt("gis_spatial_analyst")
    def prompt_spatial_analyst() -> str:
        """Configures AI assistant with best practices for spatial analysis and map automation."""
        return get_spatial_analyst_prompt()

    @server.prompt("geoprocessing_debugger")
    def prompt_debugger() -> str:
        """Guides the AI assistant in diagnosing and repairing ArcPy geoprocessing errors."""
        return get_geoprocessing_debugger_prompt()

    @server.prompt("cartography_specialist")
    def prompt_cartography_specialist() -> str:
        """Configures AI assistant for layer symbology, color ramps, labeling, and map export."""
        return get_cartography_specialist_prompt()

    return server


def main() -> None:
    """CLI entry point for running the ArcGIS Pro MCP Server."""
    parser = argparse.ArgumentParser(description="ArcGIS Pro MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for SSE or HTTP transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE or HTTP transport (default: 8000)",
    )

    args = parser.parse_args()
    server = create_server()

    if args.transport == "stdio":
        server.run(transport="stdio")
    elif args.transport == "sse":
        server.run(transport="sse", host=args.host, port=args.port)
    elif args.transport == "streamable-http":
        server.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
