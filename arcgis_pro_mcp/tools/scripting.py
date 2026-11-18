"""Dynamic ArcPy code execution tool for custom multi-step workflows."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..models import ExecuteArcPyCodeRequest
from ..services.scripting_service import ScriptingService
from ..utils import arcpy_safe


@arcpy_safe
def execute_arcpy_code(
    code: str,
    return_variables: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Executes a block of arbitrary Python/ArcPy script code and captures stdout, stderr,

    geoprocessing messages, and requested output variable values.

    Parameters:
        code: The Python script code to execute.
        return_variables: Optional list of variable names created in the script whose values should be serialized and returned.
    """
    req = ExecuteArcPyCodeRequest(
        code=code,
        return_variables=return_variables,
    )
    return ScriptingService.execute_arcpy_code(
        code=req.code,
        return_variables=req.return_variables,
    )
