# SPDX-License-Identifier: GPL-3.0-or-later
# Builds the companion only. KiCad and its official libraries remain prerequisites.
param (
    [string]$OutputDir = (Join-Path $PSScriptRoot "../../dist/windows-automation"),
    [ValidateSet("NSIS", "WIX", "ALL")]
    [string]$TargetInstaller = "ALL"
)
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)
foreach ($tool in @("python", "cmake", "cpack")) {
    if (!(Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Missing build tool: $tool" }
}
python -m PyInstaller --version
if ($LASTEXITCODE -ne 0) { throw "Install PyInstaller in the Windows build Python environment first." }
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
python -m PyInstaller --noconfirm --clean --windowed --onedir --name EMB-Automation `
    --paths $repoRoot --distpath (Join-Path $OutputDir "app") `
    --workpath (Join-Path $OutputDir "work") --specpath $OutputDir `
    (Join-Path $repoRoot "kicad_ai/studio_ui.py")
if ($LASTEXITCODE -ne 0) { throw "Application build failed" }
$cmakeBuild = Join-Path $OutputDir "cmake"
$appDir = Join-Path $OutputDir "app/EMB-Automation"
cmake -S $PSScriptRoot -B $cmakeBuild "-DEMB_APP_DIR=$appDir"
if ($LASTEXITCODE -ne 0) { throw "Packaging configuration failed" }
$generators = if ($TargetInstaller -eq "ALL") { @("NSIS", "WIX") } else { @($TargetInstaller) }
foreach ($generator in $generators) {
    cpack -G $generator --config (Join-Path $cmakeBuild "CPackConfig.cmake") -B $OutputDir
    if ($LASTEXITCODE -ne 0) { throw "$generator packaging failed. Check the matching NSIS/WiX toolchain." }
}
Write-Host "Built installers in $OutputDir. Test on a clean Windows VM with KiCad installed before distribution."
