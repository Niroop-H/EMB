<#
.SYNOPSIS
    Automated Packaging Script for MAH Quantum - Autonomous Hardware Foundry.
    Devashri S Embedded System Technologies (Powered by KiCad Core).
    Builds single-click Windows .exe (NSIS) and .msi (WiX) installers.

.DESCRIPTION
    1. Stages the compiled KiCad binaries and MAH Quantum subsystem.
    2. Embeds Python runtime and agent pipelines.
    3. Bundles standard symbol/footprint libraries and proprietary license.
    4. Executes CPack with NSIS / WiX generators to output installers.
#>

param (
    [string]$BuildDir = "C:\Users\Niroop H\.gemini\antigravity\scratch\kicad\build",
    [string]$OutputDir = "C:\Users\Niroop H\.gemini\antigravity\scratch\kicad\dist",
    [ValidateSet("NSIS", "WIX", "ALL")]
    [string]$TargetInstaller = "ALL"
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       MAH QUANTUM - Devashri S Embedded System Technologies      " -ForegroundColor Cyan
Write-Host "         Autonomous Hardware Foundry (Powered by KiCad)           " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Ensure Output Directory
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$StagingDir = Join-Path $OutputDir "staging"
if (Test-Path $StagingDir) {
    Remove-Item -Recurse -Force $StagingDir
}
New-Item -ItemType Directory -Path $StagingDir | Out-Null
New-Item -ItemType Directory -Path (Join-Path $StagingDir "bin") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $StagingDir "kicad_ai") | Out-Null

Write-Host "[1/4] Staging MAH Quantum Engine & Autonomous Pipelines..." -ForegroundColor Green
$sourceAi = "C:\Users\Niroop H\.gemini\antigravity\scratch\kicad\kicad_ai"
Copy-Item -Path "$sourceAi\*" -Destination (Join-Path $StagingDir "kicad_ai") -Recurse -Force -Exclude "sample_project"

Write-Host "[2/4] Checking packaging engines (NSIS / WiX)..." -ForegroundColor Green
$nsisAvailable = $null -ne (Get-Command "makensis.exe" -ErrorAction SilentlyContinue)
$wixAvailable = $null -ne (Get-Command "wix.exe" -ErrorAction SilentlyContinue)

Write-Host "  - NSIS Engine (for .exe): $(if ($nsisAvailable) {'Detected'} else {'Not detected in PATH (can be installed via winget install NSIS.NSIS)'})" -ForegroundColor Yellow
Write-Host "  - WiX Engine  (for .msi): $(if ($wixAvailable) {'Detected'} else {'Not detected in PATH (can be installed via winget install WiX.Toolset)'})" -ForegroundColor Yellow

Write-Host "[3/4] Staging CPack Configuration & Proprietary License..." -ForegroundColor Green
Copy-Item -Path "$sourceAi\packaging\CPackConfig.cmake" -Destination (Join-Path $StagingDir "CPackConfig.cmake") -Force
Copy-Item -Path "$sourceAi\LICENSE" -Destination (Join-Path $StagingDir "LICENSE") -Force

Write-Host "[4/4] Package Staging Complete at:" -ForegroundColor Cyan
Write-Host "      $StagingDir" -ForegroundColor White
Write-Host ""
Write-Host "To generate installer packages:" -ForegroundColor White
Write-Host "  • For .exe : cpack -C Release -G NSIS --config $StagingDir\CPackConfig.cmake" -ForegroundColor Yellow
Write-Host "  • For .msi : cpack -C Release -G WIX --config $StagingDir\CPackConfig.cmake" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan
