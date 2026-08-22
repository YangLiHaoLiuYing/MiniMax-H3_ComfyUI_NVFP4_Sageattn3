<#
 .SYNOPSIS
   Install the sageattn3 Windows cp313 wheel into a ComfyUI (portable) Python environment.

 .DESCRIPTION
   - Auto-detects python_embeded/python.exe (or use -Python to specify)
   - Installs dist/sageattn3-1.0.0-cp313-cp313-win_amd64.whl
   - Verifies the import
   - Reminds you to copy the v3 workflows into ComfyUI

 .EXAMPLE
   .\install.ps1
   .\install.ps1 -Python "D:\AI\ComfyUI\MiniMax-H3_NVFP4_v3\python_embeded\python.exe"
#>
param(
    [string]$Python = "",
    [switch]$NoVerify
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot  = Split-Path -Parent $ScriptDir

function Find-Python {
    if ($Python -and (Test-Path $Python)) { return $Python }
    $candidates = @(
        "$RepoRoot\..\python_embeded\python.exe",
        "..\python_embeded\python.exe",
        ".\python_embeded\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    )
    foreach ($c in $candidates) {
        $p = Resolve-Path $c -ErrorAction SilentlyContinue
        if ($p) { return $p.Path }
    }
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Host "❌ Cannot find Python. Specify it manually:" -ForegroundColor Red
    Write-Host "   .\install.ps1 -Python 'D:\AI\ComfyUI\xxx\python_embeded\python.exe'" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Using Python: $py" -ForegroundColor Green

$wheel = Get-ChildItem "$RepoRoot\dist\*.whl" | Select-Object -First 1
if (-not $wheel) {
    Write-Host "❌ No .whl found in dist/" -ForegroundColor Red
    exit 1
}
Write-Host "📦 Wheel: $($wheel.Name)" -ForegroundColor Cyan

Write-Host "⏳ Installing..." -ForegroundColor Yellow
& $py -m pip install --force-reinstall "$($wheel.FullName)"
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Installation failed" -ForegroundColor Red; exit 1 }

if (-not $NoVerify) {
    Write-Host "🔍 Verifying import..." -ForegroundColor Yellow
    & $py -c "import sageattn3; print('sageattn3', getattr(sageattn3,'__version__','?'), 'OK')"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Install reported success but import verification failed (possible GPU/CUDA runtime issue)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Done! Next steps:" -ForegroundColor Green
Write-Host "  1) Copy the JSON files from workflows_v3\ into <ComfyUI>/user/default/workflows/"
Write-Host "  2) Launch ComfyUI and load a v3 workflow to use FP4 acceleration"
Write-Host "  (Requires RTX 50 series / sm120, with the MiniMax-H3 model loaded)"
