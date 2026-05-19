# ALIN MSIX Build-Skript
# Aufruf: .\build_msix.ps1 [-Konfiguration Release|Debug] [-Version 1.0.0.0]
# Voraussetzung: Visual Studio 2022 oder SDK Build Tools 10.0.26100+

param(
    [string]$Konfiguration = "Release",
    [string]$Version = "1.0.0.0",
    [switch]$NurPruefen
)

$ROOT = (Resolve-Path "$PSScriptRoot\..\..").Path
$PROJEKT = "$ROOT\Windows_App\App\ALIN.csproj"
$AUSGABE = "$ROOT\Windows_App\Packaging\output"

Write-Host "=== ALIN MSIX Build ===" -ForegroundColor Cyan
Write-Host "Root:    $ROOT"
Write-Host "Projekt: $PROJEKT"
Write-Host "Version: $Version"

if ($NurPruefen) {
    Write-Host "`n[NUR-PRUEFEN] Kein Build ausgefuehrt." -ForegroundColor Yellow
    if (-not (Test-Path $PROJEKT)) { Write-Host "FEHLER: ALIN.csproj nicht gefunden" -ForegroundColor Red; exit 1 }
    if (-not (Test-Path "$ROOT\Windows_App\App\Package.appxmanifest")) { Write-Host "FEHLER: Package.appxmanifest nicht gefunden" -ForegroundColor Red; exit 1 }
    Write-Host "Alle MSIX-Skeleton-Dateien vorhanden." -ForegroundColor Green
    exit 0
}

# dotnet publish fuer MSIX
$args_build = @(
    "publish", $PROJEKT,
    "-c", $Konfiguration,
    "-r", "win-x64",
    "--self-contained", "false",
    "-p:Version=$Version",
    "-p:AppxPackageDir=$AUSGABE\",
    "-p:GenerateAppxPackageOnBuild=true",
    "-o", "$AUSGABE\app"
)

Write-Host "`nStarte Build..."
dotnet @args_build
$exit_code = $LASTEXITCODE

if ($exit_code -eq 0) {
    Write-Host "`nBuild erfolgreich: $AUSGABE" -ForegroundColor Green
    Get-ChildItem $AUSGABE -Filter "*.msix" | Select-Object Name, Length
} else {
    Write-Host "`nBuild FEHLER (Exit $exit_code)" -ForegroundColor Red
    exit $exit_code
}
