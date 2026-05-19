<#
.SYNOPSIS KM18 AUTOLAUF – OCR-Ergebnisdiagnose
.BESCHREIBUNG
  Fuehrt KM18 aus: py_compile, Selbsttest, Hauptlauf, Pruefdatei, Git-Status.
  Keine Aenderung an KM17, keine OCR-Wiederholung.
.NOTES
  Version: km18_ocr_ergebnisdiagnose_v1
#>

$ErrorActionPreference = "Stop"
$ROOT = "I:\KI_Legal_Project"
$PY = "$ROOT\Tools\Python312\python.exe"
$MOD = "$ROOT\Scripts\python_runner\km18_ocr_ergebnisdiagnose.py"
$CHK = "$ROOT\Scripts\python_runner\check_km18_ocr_ergebnisdiagnose.py"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "KM18 AUTOLAUF – OCR-ERGEBNISDIAGNOSE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$schritte = @(
    @{Name="1_py_compile"; Cmd="$PY -m py_compile `"$MOD`""; Kritisch=$true},
    @{Name="2_selbsttest"; Cmd="$PY `"$MOD`" --selftest"; Kritisch=$true},
    @{Name="3_hauptlauf"; Cmd="$PY `"$MOD`""; Kritisch=$true},
    @{Name="4_pruefdatei"; Cmd="$PY `"$CHK`""; Kritisch=$true}
)

$ergebnisse = @()
foreach($s in $schritte) {
    Write-Host "`n--- $($s.Name) ---" -ForegroundColor Yellow
    $result = Invoke-Expression $s.Cmd 2>&1
    $rc = $LASTEXITCODE
    Write-Host $result
    Write-Host "Exit: $rc"
    $ergebnisse += @{Name=$s.Name; RC=$rc; Kritisch=$s.Kritisch}
    if($s.Kritisch -and $rc -ne 0) {
        Write-Host "ABBRUCH bei $($s.Name) RC=$rc" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "KM18 AUTOLAUF ERFOLGREICH" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
$ergebnisse | Format-Table Name, RC