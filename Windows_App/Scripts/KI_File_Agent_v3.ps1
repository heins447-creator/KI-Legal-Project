param(
    [Parameter(Mandatory=$true)]
    [string]$Auftrag,

    [string[]]$Files = @(
        "Windows_App/App/MainWindow.xaml",
        "Windows_App/App/MainWindow.xaml.cs"
    ),

    [string]$Model = "qwen2.5-coder:7b",

    [int]$TimeoutSeconds = 600,

    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$Root = "I:\KI_Legal_Project"
$AllowedRoot = Join-Path $Root "Windows_App"
$Project = Join-Path $Root "Windows_App\App\KI_Legal_WindowsApp.csproj"
$LogDir = Join-Path $AllowedRoot "Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$RunLog = Join-Path $LogDir "KI_FILE_AGENT_V3_$Ts.txt"
$RawLog = Join-Path $LogDir "KI_FILE_AGENT_V3_RAW_$Ts.txt"
$BackupDir = Join-Path $LogDir "BACKUP_FILE_AGENT_V3_$Ts"

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function LogLine {
    param([string]$Text)
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $RunLog -Append
}

function Show-Phase {
    param([string]$Phase, [int]$Percent)
    Write-Progress -Activity "Lokaler KI-Datei-Agent v3" -Status $Phase -PercentComplete $Percent
}

function Assert-AllowedPath {
    param([string]$RelativePath)

    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        throw "Leerer Pfad ist unzulässig."
    }

    if ($RelativePath -match "^[A-Za-z]:") {
        throw "Absoluter Pfad ist unzulässig: $RelativePath"
    }

    if ($RelativePath -match "\.\.") {
        throw "Pfad mit .. ist unzulässig: $RelativePath"
    }

    if ($RelativePath -notlike "Windows_App/*" -and $RelativePath -notlike "Windows_App\*") {
        throw "Nur Windows_App ist erlaubt: $RelativePath"
    }

    if ($RelativePath -like "*AnythingLLM_Storage*") {
        throw "AnythingLLM_Storage ist gesperrt: $RelativePath"
    }

    $Full = [System.IO.Path]::GetFullPath((Join-Path $Root $RelativePath))
    $Allowed = [System.IO.Path]::GetFullPath($AllowedRoot)

    if (-not $Full.StartsWith($Allowed, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Pfad liegt außerhalb von Windows_App: $RelativePath"
    }

    return $Full
}

function Read-FileBlock {
    param([string]$RelativePath)

    $Full = Assert-AllowedPath $RelativePath

    if (-not (Test-Path $Full)) {
        return "===== DATEI FEHLT: $RelativePath =====`n===== ENDE DATEI: $RelativePath ====="
    }

    $Content = [System.IO.File]::ReadAllText($Full)
    return "===== DATEI: $RelativePath =====`n$Content`n===== ENDE DATEI: $RelativePath ====="
}

function Invoke-Ollama {
    param([string]$Prompt)

    $Body = @{
        model = $Model
        prompt = $Prompt
        stream = $false
        options = @{
            temperature = 0.1
            num_ctx = 16000
        }
    } | ConvertTo-Json -Depth 20

    LogLine "Ollama-Anfrage gestartet."
    LogLine "Modell: $Model"
    LogLine "Zeitlimit: $TimeoutSeconds Sekunden"

    $Job = Start-Job -ScriptBlock {
        param($BodyText)

        $Result = Invoke-RestMethod `
            -Uri "http://127.0.0.1:11434/api/generate" `
            -Method Post `
            -ContentType "application/json" `
            -Body $BodyText

        return [string]$Result.response
    } -ArgumentList $Body

    $Start = Get-Date
    $Spinner = @("|", "/", "-", "\")
    $SpinIndex = 0

    while ($Job.State -eq "Running") {
        $Elapsed = [int]((Get-Date) - $Start).TotalSeconds
        $Percent = [Math]::Min(99, [Math]::Max(1, [int](($Elapsed / $TimeoutSeconds) * 100)))
        $Spin = $Spinner[$SpinIndex % $Spinner.Length]
        $SpinIndex++

        Show-Phase -Phase "$Spin Ollama erzeugt Dateiinhalt | Laufzeit: $Elapsed s" -Percent $Percent

        if ($Elapsed % 30 -eq 0) {
            LogLine "Ollama arbeitet seit $Elapsed Sekunden."
        }

        if ($Elapsed -ge $TimeoutSeconds) {
            Stop-Job $Job -ErrorAction SilentlyContinue
            Remove-Job $Job -Force -ErrorAction SilentlyContinue
            throw "Zeitlimit erreicht: $TimeoutSeconds Sekunden. Lauf abgebrochen."
        }

        Start-Sleep -Seconds 1
    }

    $Output = Receive-Job $Job -ErrorAction Stop
    Remove-Job $Job -Force -ErrorAction SilentlyContinue

    LogLine "Ollama-Antwort erhalten."
    return ($Output -join "`n")
}

function Extract-FilesBlock {
    param([string]$Text)

    $StartMarker = "BEGIN_FILES"
    $EndMarker = "END_FILES"

    $S = $Text.IndexOf($StartMarker)
    $E = $Text.IndexOf($EndMarker)

    if ($S -lt 0 -or $E -le $S) {
        throw "Kein BEGIN_FILES/END_FILES-Block gefunden."
    }

    return $Text.Substring($S + $StartMarker.Length, $E - ($S + $StartMarker.Length)).Trim()
}

function Parse-FileBlocks {
    param([string]$Block)

    $Lines = $Block -split "\r?\n"
    $Items = New-Object System.Collections.Generic.List[object]
    $i = 0

    while ($i -lt $Lines.Count) {
        $Line = $Lines[$i]

        if ($Line -match "^FILE:\s*(.+)$") {
            $Path = $Matches[1].Trim()
            $i++

            while ($i -lt $Lines.Count -and $Lines[$i].Trim() -ne "CONTENT:") {
                $i++
            }

            if ($i -ge $Lines.Count) {
                throw "CONTENT-Marker fehlt für Datei: $Path"
            }

            $i++
            $ContentLines = New-Object System.Collections.Generic.List[string]

            while ($i -lt $Lines.Count -and $Lines[$i].Trim() -ne "END_FILE") {
                $ContentLines.Add($Lines[$i])
                $i++
            }

            if ($i -ge $Lines.Count) {
                throw "END_FILE fehlt für Datei: $Path"
            }

            $Obj = [pscustomobject]@{
                Path = $Path
                Content = ($ContentLines -join "`n")
            }

            $Items.Add($Obj)
        }

        $i++
    }

    if ($Items.Count -eq 0) {
        throw "Keine Datei-Blöcke gefunden."
    }

    return $Items
}

function Build-App {
    LogLine "Build wird gestartet."

    $Output = & dotnet build $Project 2>&1
    $Exit = $LASTEXITCODE

    $Output | Tee-Object -FilePath $RunLog -Append

    if ($Exit -ne 0) {
        throw "Build fehlgeschlagen. ExitCode: $Exit"
    }

    LogLine "Build erfolgreich."
}

function Restore-Backups {
    param([array]$BackupItems)

    LogLine "Rollback wird ausgeführt."

    foreach ($Item in $BackupItems) {
        if ($Item.ExistedBefore) {
            Copy-Item -LiteralPath $Item.BackupPath -Destination $Item.TargetPath -Force
            LogLine "Wiederhergestellt: $($Item.TargetPath)"
        }
        else {
            Remove-Item -LiteralPath $Item.TargetPath -Force -ErrorAction SilentlyContinue
            LogLine "Neu erzeugte Datei entfernt: $($Item.TargetPath)"
        }
    }
}

try {
    Show-Phase -Phase "Phase 1/5: Kontext einlesen" -Percent 5
    LogLine "KI-Datei-Agent v3 gestartet."
    LogLine "Auftrag: $Auftrag"
    LogLine "Erlaubter Bereich: $AllowedRoot"

    $ContextParts = New-Object System.Collections.Generic.List[string]

    foreach ($F in $Files) {
        LogLine "Kontextdatei: $F"
        $ContextParts.Add((Read-FileBlock $F))
    }

    $Context = $ContextParts -join "`n`n"

    $Prompt = @"
Du bist ein lokaler KI-Programmierer für eine Windows-WPF-App.

Arbeitsregeln:
- Arbeite ausschließlich unter Windows_App.
- Keine Cloud.
- Keine GitHub-Verbindung.
- Keine externen Repositories.
- Keine Zugangsdaten.
- Keine Änderungen an AnythingLLM_Storage.
- Gib vollständige Dateiinhalt-Blöcke aus.
- Keine Erklärungen außerhalb von BEGIN_FILES und END_FILES.
- Keine Markdown-Codeblöcke.
- Ändere nur Dateien, die für den Auftrag erforderlich sind.
- Wenn nur eine Datei genannt ist, ändere nur diese Datei.

Antwortformat zwingend:
BEGIN_FILES
FILE: Windows_App/App/MainWindow.xaml
CONTENT:
vollständiger Dateiinhalt
END_FILE
END_FILES

AUFTRAG:
$Auftrag

AKTUELLER DATEISTAND:
$Context
"@

    Show-Phase -Phase "Phase 2/5: Ollama erzeugt Dateiinhalt" -Percent 10

    $Response = Invoke-Ollama -Prompt $Prompt
    $Response | Set-Content -LiteralPath $RawLog -Encoding UTF8

    Show-Phase -Phase "Phase 3/5: Antwort prüfen" -Percent 70

    $FileBlock = Extract-FilesBlock $Response
    $NewFiles = Parse-FileBlocks $FileBlock

    $Backups = New-Object System.Collections.Generic.List[object]

    Show-Phase -Phase "Phase 4/5: Dateien schreiben" -Percent 80

    foreach ($F in $NewFiles) {
        $Rel = [string]$F.Path
        $Content = [string]$F.Content
        $Target = Assert-AllowedPath $Rel

        $TargetDir = Split-Path -Parent $Target
        New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

        $SafeName = ($Rel -replace "[:\\\/]", "_")
        $BackupPath = Join-Path $BackupDir $SafeName

        $Existed = Test-Path $Target

        if ($Existed) {
            Copy-Item -LiteralPath $Target -Destination $BackupPath -Force
        }

        $Backups.Add([pscustomobject]@{
            TargetPath = $Target
            BackupPath = $BackupPath
            ExistedBefore = $Existed
        })

        [System.IO.File]::WriteAllText($Target, $Content, $Utf8NoBom)
        LogLine "Datei geschrieben: $Target"
    }

    if (-not $NoBuild) {
        Show-Phase -Phase "Phase 5/5: Build prüfen" -Percent 90

        try {
            Build-App
        }
        catch {
            LogLine "Buildfehler nach KI-Änderung: $($_.Exception.Message)"
            Restore-Backups -BackupItems $Backups
            Build-App
            throw "KI-Änderung wurde wegen Buildfehler zurückgerollt."
        }
    }

    Show-Phase -Phase "Fertig" -Percent 100
    Write-Progress -Activity "Lokaler KI-Datei-Agent v3" -Completed

    LogLine "Git-Status:"
    git -C $Root status --short 2>&1 | Tee-Object -FilePath $RunLog -Append

    LogLine "KI-Datei-Agent v3 beendet."

    Write-Host ""
    Write-Host "Fertig. Protokoll:"
    Write-Host $RunLog
    Write-Host ""
    Write-Host "Rohantwort:"
    Write-Host $RawLog
}
catch {
    Write-Progress -Activity "Lokaler KI-Datei-Agent v3" -Completed
    LogLine "FEHLER: $($_.Exception.Message)"
    throw
}
