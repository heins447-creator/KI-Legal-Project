$ErrorActionPreference = "Stop"
$ProjektPython = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$ApiDatei = "I:\KI_Legal_Project\ALIN_Neustart_Core\25_API_Backend\alin_api_main.py"

Write-Host "ALIN FastAPI-Backend wird gestartet ..."
Write-Host "URL: http://127.0.0.1:8744"
Write-Host "Docs: http://127.0.0.1:8744/docs"
Write-Host "Druecken Sie STRG+C zum Beenden."
Write-Host ""

& $ProjektPython -m uvicorn alin_api_main:app --host 127.0.0.1 --port 8744 --app-dir "I:\KI_Legal_Project\ALIN_Neustart_Core\25_API_Backend"
