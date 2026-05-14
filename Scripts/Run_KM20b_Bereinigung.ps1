# KM20b – Testdummy-Ausschluss
# PowerShell-Starter V1

$root = "I:\KI_Legal_Project"
$python = "$root\Tools\Python312\python.exe"
$runner = "$root\Scripts\python_runner\km20b_testdummy_ausschliessen.py"
$pruefung = "$root\Scripts\python_runner\km20_pruefung.py"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=" * 60
Write-Host "KM20b – TESTDUMMY AUSSCHLIESSEN"
Write-Host "=" * 60

try {
    Write-Host "[Step 1/2] KM20b – Bereinigung..."
    $out = & $python $runner 2>&1
    if ($LASTEXITCODE -ne 0) { throw "KM20b fehlgeschlagen" }

    Write-Host "[Step 2/2] Pruefdatei..."
    $out = & $python $pruefung 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Host "PRUEFUNG FEHLER"; exit 1 }

    Write-Host "KM20b ERFOLGREICH – 24 Seiten, 3 Originale"
} catch {
    Write-Host "ABBruch: $_"
    exit 1
}
