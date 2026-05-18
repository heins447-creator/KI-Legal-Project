#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    CORE-22 – Agenten-Einstieg und Arbeitsregel-Erzwingung
.DESCRIPTION
    Prüft Arbeitsindex, Startpunkt und Pfad-Berechtigungen.
    Erzeugt Regeldatei für Roo.
#>
$ErrorActionPreference = 'Stop'
$python = 'I:\KI_Legal_Project\Tools\Python312\python.exe'
$root = 'I:\KI_Legal_Project'

Write-Host '[CORE-22] Starte Agenten-Einstieg...' -ForegroundColor Cyan

# 1. py_compile
Write-Host '[CORE-22] py_compile...' -ForegroundColor Yellow
& $python -m py_compile "$root\Scripts\python_runner\core22_agenten_einstieg.py"
if ($LASTEXITCODE -ne 0) { throw 'py_compile fehlgeschlagen' }
& $python -m py_compile "$root\Scripts\python_runner\check_core22_agenten_einstieg.py"
if ($LASTEXITCODE -ne 0) { throw 'py_compile check fehlgeschlagen' }
Write-Host '[CORE-22] py_compile BESTANDEN' -ForegroundColor Green

# 2. Runner
Write-Host '[CORE-22] Führe Runner aus...' -ForegroundColor Yellow
& $python "$root\Scripts\python_runner\core22_agenten_einstieg.py"
if ($LASTEXITCODE -ne 0) { throw 'Runner fehlgeschlagen' }
Write-Host '[CORE-22] Runner BESTANDEN' -ForegroundColor Green

# 3. Check
Write-Host '[CORE-22] Führe Check aus...' -ForegroundColor Yellow
& $python "$root\Scripts\python_runner\check_core22_agenten_einstieg.py"
if ($LASTEXITCODE -ne 0) { throw 'Check fehlgeschlagen' }
Write-Host '[CORE-22] Check BESTANDEN' -ForegroundColor Green

Write-Host '[CORE-22] ABGESCHLOSSEN' -ForegroundColor Green
