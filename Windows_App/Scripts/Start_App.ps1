param()

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Project = Join-Path $Root "App\KI_Legal_WindowsApp.csproj"
$LogDir = Join-Path $Root "Logs"
$Log = Join-Path $LogDir "START_LOG.txt"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

"Start: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $Log -Encoding UTF8
dotnet run --project $Project 2>&1 | Tee-Object -FilePath $Log -Append
