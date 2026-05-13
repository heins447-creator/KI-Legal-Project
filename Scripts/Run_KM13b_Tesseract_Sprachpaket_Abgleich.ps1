# -*- coding: utf-8 -*-
# PowerShell 5.1+ Starter fuer KM13b
<#
.SYNOPSIS
    KM13b – Tesseract-Sprachpaket-Abgleich
.DESCRIPTION
    Prueft Tesseract-Installationen, Sprachpakete und gleicht mit KM13-Config ab.
    KEINE Installation, KEIN Internet, KEINE Originalaenderung.
#>
param(
    [switch]$OnlySelfTest,
    [switch]$SkipSelfTest,
    [switch]$SkipCheck
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
try { chcp.com 65001 | Out-Null } catch {}
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}
$ProjectRoot = "I:\KI_Legal_Project"
$LogRoot = Join-Path $ProjectRoot "Agentensteuerung\13b_Tesseract_Sprachpaket_Abgleich\90_RunLogs"
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogRoot "RUN_KM13b_$Stamp.log"
$Python = Join-Path $ProjectRoot "Tools\Python312\python.exe"
$Runner = Join-Path $ProjectRoot "Scripts\python_runner\km13b_tesseract_sprachpaket_abgleich.py"
$Check  = Join-Path $ProjectRoot "Scripts\python_runner\check_km13b_tesseract_sprachpaket_abgleich.py"
Push-Location -LiteralPath $ProjectRoot
Add-Content -LiteralPath $LogFile -Value "KM13b START" -Encoding UTF8
if (-not (Test-Path $Python)) { throw "Python nicht gefunden: $Python" }
if (-not (Test-Path $Runner)) { throw "Runner fehlt: $Runner" }
if (-not (Test-Path $Check))  { throw "Check fehlt: $Check" }
try {
    & $Python -m py_compile $Runner 2>&1 | Out-File -LiteralPath $LogFile -Append -Encoding UTF8
    if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }
    if ($OnlySelfTest) {
        & $Python $Runner --selftest 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -ne 0) { throw "Selbsttest fehlgeschlagen" }
        Pop-Location
        exit 0
    }
    if (-not $SkipSelfTest) {
        & $Python $Runner --selftest 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -ne 0) { throw "Selbsttest fehlgeschlagen" }
    }
    & $Python $Runner 2>&1 | Tee-Object -FilePath $LogFile -Append
    if ($LASTEXITCODE -ne 0) { throw "Hauptlauf fehlgeschlagen" }
    if (-not $SkipCheck) {
        & $Python $Check 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -ne 0) { throw "Pruefdatei fehlgeschlagen" }
    }
    Add-Content -LiteralPath $LogFile -Value "KM13b ERFOLGREICH" -Encoding UTF8
    Write-Host "KM13b ERFOLGREICH" -ForegroundColor Green
    Write-Host "Log: $LogFile"
    Write-Host "Naechster: KM15 – Arbeitsuebersetzungsschicht"
    Pop-Location
    exit 0
}
catch {
    Add-Content -LiteralPath $LogFile -Value "KM13b FEHLER: $_" -Encoding UTF8
    Write-Host "KM13b FEHLER: $_" -ForegroundColor Red
    Write-Host "Log: $LogFile"
    Pop-Location
    exit 1
}
