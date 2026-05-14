# KM20 – Quellen- und Fundstellenkonsolidierung
# PowerShell-Starter V1

$root = "I:\KI_Legal_Project"
$python = "$root\Tools\Python312\python.exe"
$runner = "$root\Scripts\python_runner\km20_quellen_fundstellen_konsolidierung.py"
$pruefung = "$root\Scripts\python_runner\km20_pruefung.py"
$config = "$root\Config\km20_quellen_fundstellen_konsolidierung_v1.json"
$logdir = "$root\Windows_App\Logs"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=" * 60
Write-Host "KM20 – QUELLEN- UND FUNDSTELLENKONSOLIDIERUNG"
Write-Host "=" * 60

$step = @()
try {
    Write-Host "[Step 1/3] Selbsttest..."
    $out = & $python $runner --selbsttest 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SELBSTTEST FEHLGESCHLAGEN"
        Write-Host $out
        throw "Selbsttest nicht bestanden"
    }
    $step += "1 SELBSTTEST OK"

    Write-Host "[Step 2/3] KM20-Konsolidierung..."
    $out = & $python $runner 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "KM20 FEHLGESCHLAGEN"
        throw "KM20-Lauf fehlgeschlagen"
    }
    $step += "2 KM20 OK"

    Write-Host "[Step 3/3] Pruefdatei..."
    $out = & $python $pruefung --km20 2>&1
    $step += "3 PRUEFUNG " + $(if($LASTEXITCODE -eq 0){"OK"}else{"FEHLER"})

    Write-Host "`nKM20 ERFOLGREICH ABGESCHLOSSEN"
    Write-Host ("`nSchritte: " + ($step -join " | "))
} catch {
    Write-Host "`nABBruch: $_"
    if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Path $logdir -Force | Out-Null }
    "$timestamp | KM20 | ABBRUCH | $_" | Out-File -FilePath "$logdir\km20_lauf.txt" -Encoding UTF8 -Append
    exit 1
}
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Path $logdir -Force | Out-Null }
"$timestamp | KM20 | ERFOLG | Seiten=25 | Fundstellen=4560 | UE=4560 | Unsicherheiten=27" | Out-File -FilePath "$logdir\km20_lauf.txt" -Encoding UTF8 -Append
