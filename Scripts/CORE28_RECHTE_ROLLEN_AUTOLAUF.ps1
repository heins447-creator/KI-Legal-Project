#Requires -Version 5.1
<#
.SYNOPSIS
    CORE-28: Rechte und Rollen – PowerShell-Autostarter
.DESCRIPTION
    Führt den Python-Runner core28_rechte_rollen.py aus und prüft,
    ob der Bericht anschließend existiert.
.NOTES
    Modul: CORE-28
    Name:   Rechte und Rollen
#>
$ErrorActionPreference = "Stop"

$python = "python"
$runner = "Scripts\python_runner\core28_rechte_rollen.py"
$bericht = "ALIN_Neustart_Core\Reports\CORE28_RECHTE_ROLLEN_BERICHT.txt"

function Test-Bericht {
    if (Test-Path $bericht) {
        $inhalt = Get-Content $bericht -Raw
        if ($inhalt -match "Status:\s*ERFOLG") {
            return $true
        }
    }
    return $false
}

Write-Host "============================================"
Write-Host "CORE-28: Rechte und Rollen"
Write-Host "============================================"

# 1. py_compile
Write-Host "[1/4] py_compile auf Runner..."
& $python -m py_compile $runner
if ($LASTEXITCODE -ne 0) { throw "py_compile fehlgeschlagen" }
Write-Host "      OK"

# 2. Check
Write-Host "[2/4] Check ausführen..."
& $python "Scripts\python_runner\check_core28_rechte_rollen.py"
if ($LASTEXITCODE -ne 0) { throw "Check fehlgeschlagen" }
Write-Host "      OK"

# 3. Runner
Write-Host "[3/4] Runner ausführen..."
& $python $runner
if ($LASTEXITCODE -ne 0) { throw "Runner fehlgeschlagen" }
Write-Host "      OK"

# 4. Bericht prüfen
Write-Host "[4/4] Bericht prüfen..."
if (Test-Bericht) {
    Write-Host "      OK – Bericht zeigt ERFOLG"
} else {
    throw "Bericht zeigt FEHLER oder fehlt"
}

Write-Host ""
Write-Host "============================================"
Write-Host "CORE-28: ERFOLG – alle Prüfungen bestanden"
Write-Host "============================================"
