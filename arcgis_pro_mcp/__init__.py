"""ArcGIS Pro Model Context Protocol (MCP) Server.

Enables AI coding assistants and LLMs to interact with ArcGIS Pro and ArcPy.
"""

from .server import create_server, main

__version__ = "1.0.0"
__all__ = ["create_server", "main"]
