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
$LogDir = Join-Path $AllowedRoot "Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$RunLog = Join-Path $LogDir "KI_PATCH_AGENT_V2_$Ts.txt"
$RawLog = Join-Path $LogDir "KI_PATCH_AGENT_V2_RAW_$Ts.txt"
$PatchFile = Join-Path $LogDir "KI_PATCH_AGENT_V2_$Ts.patch"

function LogLine {
    param([string]$Text)
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $RunLog -Append
}

function Show-Phase {
    param(
        [string]$Phase,
        [int]$Percent
    )

    Write-Progress `
        -Activity "Lokaler KI-Patch-Agent v2" `
        -Status $Phase `
        -PercentComplete $Percent
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

    $Content = Get-Content -LiteralPath $Full -Raw -Encoding UTF8
    return "===== DATEI: $RelativePath =====`n$Content`n===== ENDE DATEI: $RelativePath ====="
}

function Invoke-OllamaWithProgress {
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
    LogLine "Adresse: http://127.0.0.1:11434/api/generate"
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

        if ($TimeoutSeconds -gt 0) {
            $Percent = [Math]::Min(99, [Math]::Max(1, [int](($Elapsed / $TimeoutSeconds) * 100)))
        }
        else {
            $Percent = 50
        }

        $Spin = $Spinner[$SpinIndex % $Spinner.Length]
        $SpinIndex++

        Show-Phase -Phase "$Spin Ollama erzeugt Patch | Laufzeit: $Elapsed s | Ziel: $($Files -join ', ')" -Percent $Percent

        if ($Elapsed % 30 -eq 0) {
            LogLine "Ollama arbeitet seit $Elapsed Sekunden. Phase: Patch-Erzeugung."
        }

        if ($TimeoutSeconds -gt 0 -and $Elapsed -ge $TimeoutSeconds) {
            Stop-Job $Job -ErrorAction SilentlyContinue
            Remove-Job $Job -Force -ErrorAction SilentlyContinue
            throw "Zeitlimit erreicht: $TimeoutSeconds Sekunden. Der KI-Lauf wurde abgebrochen."
        }

        Start-Sleep -Seconds 1
    }

    Show-Phase -Phase "Ollama-Antwort wird übernommen" -Percent 99

    $Output = Receive-Job $Job -ErrorAction Stop
    Remove-Job $Job -Force -ErrorAction SilentlyContinue

    LogLine "Ollama-Antwort erhalten."

    return ($Output -join "`n")
}

function Extract-Patch {
    param([string]$Text)

    $StartMarker = "BEGIN_PATCH"
    $EndMarker = "END_PATCH"

    $S = $Text.IndexOf($StartMarker)
    $E = $Text.IndexOf($EndMarker)

    if ($S -lt 0 -or $E -le $S) {
        throw "Kein BEGIN_PATCH/END_PATCH-Block gefunden."
    }

    $Patch = $Text.Substring($S + $StartMarker.Length, $E - ($S + $StartMarker.Length)).Trim()

    if ([string]::IsNullOrWhiteSpace($Patch)) {
        throw "Patch ist leer."
    }

    return $Patch
}

function Validate-Patch {
    param([string]$Patch)

    $Lines = $Patch -split "`n"

    foreach ($Line in $Lines) {
        $L = $Line.Trim()

        if ($L -match "^(diff --git a/)(.+?)( b/)(.+)$") {
            Assert-AllowedPath $Matches[2] | Out-Null
            Assert-AllowedPath $Matches[4] | Out-Null
        }

        if ($L -match "^(--- a/)(.+)$") {
            Assert-AllowedPath $Matches[2] | Out-Null
        }

        if ($L -match "^(\+\+\+ b/)(.+)$") {
            Assert-AllowedPath $Matches[2] | Out-Null
        }

        if ($L -like "*AnythingLLM_Storage*") {
            throw "Patch enthält gesperrten Pfad AnythingLLM_Storage."
        }
    }
}

try {
    Show-Phase -Phase "Phase 1/5: Kontext einlesen" -Percent 5
    LogLine "KI-Patch-Agent v2 gestartet."
    LogLine "Auftrag: $Auftrag"
    LogLine "Erlaubter Bereich: $AllowedRoot"

    $ContextParts = New-Object System.Collections.Generic.List[string]

    foreach ($F in $Files) {
        LogLine "Kontextdatei: $F"
        $ContextParts.Add((Read-FileBlock $F))
    }

    $Context = $ContextParts -join "`n`n"

    Show-Phase -Phase "Phase 2/5: Patch durch Ollama erzeugen" -Percent 10

    $Prompt = @"
Du bist ein lokaler KI-Programmierer für eine Windows-WPF-App.

Arbeitsregeln:
- Arbeite ausschließlich unter Windows_App.
- Keine Cloud.
- Keine GitHub-Verbindung.
- Keine externen Repositories.
- Keine Zugangsdaten.
- Keine Änderungen an AnythingLLM_Storage.
- Erzeuge ausschließlich einen Unified-Diff-Patch.
- Keine Erklärung außerhalb des Patch-Blocks.
- Keine Markdown-Codeblöcke.
- Nur notwendige Änderungen.
- Halte Änderungen klein.
- Bevorzuge wenige, sichere Änderungen.
- Gib keine ganze Datei aus, sondern nur einen Unified-Diff-Patch.

Antwortformat zwingend:
BEGIN_PATCH
diff --git a/Windows_App/App/MainWindow.xaml b/Windows_App/App/MainWindow.xaml
--- a/Windows_App/App/MainWindow.xaml
+++ b/Windows_App/App/MainWindow.xaml
@@ ...
...
END_PATCH

AUFTRAG:
$Auftrag

AKTUELLER DATEISTAND:
$Context
"@

    $Response = Invoke-OllamaWithProgress -Prompt $Prompt
    $Response | Set-Content -LiteralPath $RawLog -Encoding UTF8

    Show-Phase -Phase "Phase 3/5: Patch aus Antwort auslesen" -Percent 75

    $Patch = Extract-Patch $Response
    Validate-Patch $Patch
    $Patch | Set-Content -LiteralPath $PatchFile -Encoding UTF8

    LogLine "Patch gespeichert: $PatchFile"

    Show-Phase -Phase "Phase 4/5: Patch prüfen und anwenden" -Percent 85

    git -C $Root apply --check $PatchFile
    if ($LASTEXITCODE -ne 0) {
        throw "Patchprüfung fehlgeschlagen. Der Patch wurde nicht angewendet. Patchdatei: $PatchFile"
    }

    git -C $Root apply --whitespace=nowarn $PatchFile
    if ($LASTEXITCODE -ne 0) {
        throw "Patchanwendung fehlgeschlagen. Arbeitsstand unverändert prüfen. Patchdatei: $PatchFile"
    }

    LogLine "Patch angewendet."

    if (-not $NoBuild) {
        Show-Phase -Phase "Phase 5/5: Build prüfen" -Percent 92

        $Build = Join-Path $AllowedRoot "Scripts\Build_App.ps1"

        if (Test-Path $Build) {
            LogLine "Build wird gestartet."
            & $Build 2>&1 | Tee-Object -FilePath $RunLog -Append
            LogLine "Build beendet."
        }
        else {
            LogLine "Buildskript nicht gefunden: $Build"
        }
    }

    Show-Phase -Phase "Fertig" -Percent 100
    Write-Progress -Activity "Lokaler KI-Patch-Agent v2" -Completed

    LogLine "Git-Status:"
    git -C $Root status --short 2>&1 | Tee-Object -FilePath $RunLog -Append

    LogLine "KI-Patch-Agent v2 beendet."

    Write-Host ""
    Write-Host "Fertig. Protokoll:"
    Write-Host $RunLog
    Write-Host ""
    Write-Host "Rohantwort:"
    Write-Host $RawLog
    Write-Host ""
    Write-Host "Patch:"
    Write-Host $PatchFile
}
catch {
    Write-Progress -Activity "Lokaler KI-Patch-Agent v2" -Completed
    LogLine "FEHLER: $($_.Exception.Message)"
    throw
}


