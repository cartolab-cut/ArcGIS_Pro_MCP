# PowerShell launcher for ArcGIS Pro MCP Server
[CmdletBinding()]
param(
    [string]$Transport = "stdio",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $ScriptDir "run_server.py"

# Locate ArcGIS Pro Python
$ProPython = "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"

if (-not (Test-Path $ProPython)) {
    $Propy = "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
    if (Test-Path $Propy) {
        & $Propy $ServerScript --transport $Transport --host $HostAddress --port $Port
        exit $LASTEXITCODE
    }
    $ProPython = (Get-Command python -ErrorAction SilentlyContinue).Source
}

& $ProPython $ServerScript --transport $Transport --host $HostAddress --port $Port
