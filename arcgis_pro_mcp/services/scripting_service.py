"""Dynamic ArcPy code execution service for custom multi-step workflows."""

from __future__ import annotations
import io
import sys
import traceback
from typing import Any, Dict, List, Optional
import arcpy

from .. import config
from ..utils import capture_arcpy_messages


class ScriptingService:
    """Service layer encapsulating dynamic execution of ArcPy code blocks."""

    @staticmethod
    def execute_arcpy_code(
        code: str,
        return_variables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Executes a block of arbitrary Python/ArcPy script code and captures stdout, stderr, and variables."""
        if not getattr(config, "ENABLE_ARCPY_EXEC", True):
            return {
                "success": False,
                "error": "Execution of dynamic ArcPy code is disabled by configuration (ENABLE_ARCPY_EXEC=False).",
            }

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        execution_context = {
            "arcpy": arcpy,
            "__name__": "__main__",
        }

        try:
            exec(code, execution_context)
            exec_error = None
        except Exception as e:
            exec_error = {
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc(),
            }
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        captured_out = stdout_capture.getvalue()
        captured_err = stderr_capture.getvalue()
        gp_msgs = capture_arcpy_messages()

        variables_result = {}
        if return_variables:
            for var_name in return_variables:
                if var_name in execution_context:
                    val = execution_context[var_name]
                    try:
                        if isinstance(val, (str, int, float, bool, list, dict, type(None))):
                            variables_result[var_name] = val
                        else:
                            variables_result[var_name] = str(val)
                    except Exception:
                        variables_result[var_name] = str(val)

        if exec_error:
            return {
                "success": False,
                "stdout": captured_out,
                "stderr": captured_err,
                "geoprocessing_messages": gp_msgs,
                "execution_error": exec_error,
            }

        return {
            "success": True,
            "stdout": captured_out,
            "stderr": captured_err,
            "geoprocessing_messages": gp_msgs,
            "variables": variables_result,
        }
