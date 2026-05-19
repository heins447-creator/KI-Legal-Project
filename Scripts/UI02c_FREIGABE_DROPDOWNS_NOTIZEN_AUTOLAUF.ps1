# UI02c Freigabe Dropdowns Notizen – PowerShell Starter
$ScriptDir = "I:\KI_Legal_Project\Scripts\python_runner"
$Python = "I:\KI_Legal_Project\Tools\Python312\python.exe"

Write-Host "UI02c FREIGABE DROPDOWNS NOTIZEN AUTOLAUF" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. py_compile
Write-Host "`n[1/5] py_compile ..." -ForegroundColor Yellow
& $Python -m py_compile "$ScriptDir\ui02c_freigabe_dropdowns_notizen.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: py_compile fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "       OK" -ForegroundColor Green

# 2. Selbsttest
Write-Host "`n[2/5] Selbsttest ..." -ForegroundColor Yellow
& $Python "$ScriptDir\ui02c_freigabe_dropdowns_notizen.py" --selbsttest
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Selbsttest fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "       OK" -ForegroundColor Green

# 3. Hauptlauf
Write-Host "`n[3/5] Hauptlauf ..." -ForegroundColor Yellow
& $Python "$ScriptDir\ui02c_freigabe_dropdowns_notizen.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Hauptlauf mit Fehler (Exit=$LASTEXITCODE)" -ForegroundColor Red
    # Nicht abbrechen – Pruefdatei trotzdem
} else {
    Write-Host "       OK" -ForegroundColor Green
}

# 4. Pruefdatei
Write-Host "`n[4/5] Pruefdatei ..." -ForegroundColor Yellow
& $Python "$ScriptDir\check_ui02c_freigabe_dropdowns_notizen.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Pruefdatei nicht bestanden" -ForegroundColor Red
} else {
    Write-Host "       OK" -ForegroundColor Green
}

# 5. Logs
Write-Host "`n[5/5] Logs schreiben ..." -ForegroundColor Yellow
$LogDir = "I:\KI_Legal_Project\Agentensteuerung\UI02_Tuerschwelle_Bau\17_Freigabe_UI02c\90_RunLogs"
$LogFile = "$LogDir\UI02c_AUTOLAUF_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
"UI02c AUTOLAUF $((Get-Date).ToString('o'))" | Out-File -FilePath $LogFile -Encoding utf8
"Exit py_compile: $LASTEXITCODE" | Out-File -FilePath $LogFile -Append -Encoding utf8
Get-ChildItem "I:\KI_Legal_Project\Agentensteuerung\UI02_Tuerschwelle_Bau\17_Freigabe_UI02c" -Recurse -File | ForEach-Object {
    "$($_.FullName.Replace('I:\KI_Legal_Project\','')) : $($_.Length) bytes" | Out-File -FilePath $LogFile -Append -Encoding utf8
}
Write-Host "       Log: $LogFile" -ForegroundColor Gray

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "UI02c AUTOLAUF BEENDET" -ForegroundColor Cyan
Write-Host "Browseransicht:" -ForegroundColor White
Write-Host "  I:\KI_Legal_Project\Agentensteuerung\UI02_Tuerschwelle_Bau\17_Freigabe_UI02c\12_Browseransicht\index.html" -ForegroundColor Gray
