param(
    [Parameter(Mandatory=$true)]
    [string]$Auftrag,

    [string]$Model = "qwen2.5-coder:1.5b",

    [int]$MaxRunden = 4,

    [int]$TimeoutSeconds = 180,

    [switch]$AutoCommit,

    [switch]$StartAppNachErfolg
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$Root = "I:\KI_Legal_Project"
$WinRoot = Join-Path $Root "Windows_App"
$ScriptDir = Join-Path $WinRoot "Scripts"
$LogDir = Join-Path $WinRoot "Logs"
$BuildScript = Join-Path $ScriptDir "Build_App.ps1"
$StartScript = Join-Path $ScriptDir "Start_App.ps1"
$Agent = Join-Path $ScriptDir "KI_Aenderungs_Agent_v4.ps1"

$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$RunLog = Join-Path $LogDir "KI_AUTOPILOT_V5_$Ts.txt"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

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
        -Activity "Lokaler KI-Autopilot v5" `
        -Status $Phase `
        -PercentComplete $Percent
}

function Get-GitShortStatus {
    return (git -C $Root status --short 2>&1 | Out-String).Trim()
}

function Run-Build {
    LogLine "Buildprüfung wird gestartet."

    $Output = & $BuildScript 2>&1
    $ExitCode = $LASTEXITCODE

    $Output | Tee-Object -FilePath $RunLog -Append

    if ($ExitCode -ne 0) {
        return [pscustomobject]@{
            Ok = $false
            Text = ($Output | Out-String)
        }
    }

    return [pscustomobject]@{
        Ok = $true
        Text = ($Output | Out-String)
    }
}

function Run-AgentRound {
    param(
        [string]$RoundAuftrag,
        [int]$Runde
    )

    LogLine "Runde $Runde gestartet."
    LogLine "Auftrag Runde $Runde:"
    LogLine $RoundAuftrag

    $AgentOutput = ""
    $AgentOk = $true

    try {
        $Output = & $Agent `
            -Model $Model `
            -Auftrag $RoundAuftrag `
            -Files "Windows_App/App/MainWindow.xaml","Windows_App/App/MainWindow.xaml.cs" `
            -TimeoutSeconds $TimeoutSeconds 2>&1

        $AgentOutput = ($Output | Out-String)
        $AgentOutput | Tee-Object -FilePath $RunLog -Append
    }
    catch {
        $AgentOk = $false
        $AgentOutput = ($_ | Out-String)
        $AgentOutput | Tee-Object -FilePath $RunLog -Append
    }

    return [pscustomobject]@{
        Ok = $AgentOk
        Text = $AgentOutput
    }
}

function Build-FollowupAuftrag {
    param(
        [string]$OriginalAuftrag,
        [string]$LetzterFehler,
        [string]$GitStatus,
        [int]$Runde
    )

    return @"
Der vorherige automatische Änderungsversuch ist fehlgeschlagen oder unvollständig.

Ursprünglicher Auftrag:
$OriginalAuftrag

Fehler- oder Rückmeldung:
$LetzterFehler

Aktueller Git-Status:
$GitStatus

Neuer Auftrag:
Korrigiere den vorherigen Versuch mit der kleinstmöglichen sicheren Änderung.
Verwende nur kleine Änderungsbefehle.
Ändere nur Dateien unter Windows_App.
Ändere bevorzugt nur MainWindow.xaml und nur falls zwingend notwendig MainWindow.xaml.cs.
Keine Änderungen an AnythingLLM_Storage.
Keine Cloud.
Keine GitHub-Verbindung.
Achte darauf, daß der Build danach erfolgreich bleibt.
"@
}

function Commit-Success {
    param([string]$Message)

    $Status = Get-GitShortStatus

    if ([string]::IsNullOrWhiteSpace($Status)) {
        LogLine "Kein Commit nötig. Git-Status ist sauber."
        return
    }

    LogLine "AutoCommit ist aktiv. Änderungen werden lokal gesichert."
    git -C $Root add Windows_App/App/MainWindow.xaml Windows_App/App/MainWindow.xaml.cs 2>&1 | Tee-Object -FilePath $RunLog -Append

    $SafeMessage = $Message
    if ($SafeMessage.Length -gt 120) {
        $SafeMessage = $SafeMessage.Substring(0, 120)
    }

    git -C $Root commit -m "Autopilot: $SafeMessage" 2>&1 | Tee-Object -FilePath $RunLog -Append
}

try {
    if (-not (Test-Path $Agent)) {
        throw "KI_Aenderungs_Agent_v4.ps1 wurde nicht gefunden: $Agent"
    }

    if (-not (Test-Path $BuildScript)) {
        throw "Build_App.ps1 wurde nicht gefunden: $BuildScript"
    }

    Show-Phase -Phase "Startprüfung" -Percent 2

    LogLine "KI-Autopilot v5 gestartet."
    LogLine "Modell: $Model"
    LogLine "MaxRunden: $MaxRunden"
    LogLine "TimeoutSeconds je Runde: $TimeoutSeconds"
    LogLine "Auftrag: $Auftrag"

    $StartStatus = Get-GitShortStatus

    if (-not [string]::IsNullOrWhiteSpace($StartStatus)) {
        LogLine "WARNUNG: Arbeitsstand war beim Start nicht sauber:"
        LogLine $StartStatus
    }
    else {
        LogLine "Startstatus: Git-Arbeitsstand sauber."
    }

    $CurrentAuftrag = $Auftrag
    $FinalOk = $false
    $LastError = ""

    for ($Runde = 1; $Runde -le $MaxRunden; $Runde++) {
        $Percent = [int](($Runde - 1) / [Math]::Max(1, $MaxRunden) * 80) + 5
        Show-Phase -Phase "Runde $Runde von $MaxRunden: KI ändert Dateien" -Percent $Percent

        $AgentResult = Run-AgentRound -RoundAuftrag $CurrentAuftrag -Runde $Runde

        $GitStatus = Get-GitShortStatus
        LogLine "Git-Status nach Runde $Runde:"
        LogLine $GitStatus

        Show-Phase -Phase "Runde $Runde: Build prüfen" -Percent ($Percent + 10)

        $BuildResult = Run-Build

        if ($AgentResult.Ok -and $BuildResult.Ok) {
            LogLine "Runde $Runde erfolgreich. Build ist fehlerfrei."
            $FinalOk = $true
            break
        }

        $LastError = @"
Agent OK: $($AgentResult.Ok)
Build OK: $($BuildResult.Ok)

Agent-Ausgabe:
$($AgentResult.Text)

Build-Ausgabe:
$($BuildResult.Text)
"@

        LogLine "Runde $Runde war nicht erfolgreich."
        LogLine $LastError

        $CurrentAuftrag = Build-FollowupAuftrag `
            -OriginalAuftrag $Auftrag `
            -LetzterFehler $LastError `
            -GitStatus $GitStatus `
            -Runde $Runde
    }

    if (-not $FinalOk) {
        throw "Autopilot konnte den Auftrag nach $MaxRunden Runden nicht erfolgreich abschließen."
    }

    Show-Phase -Phase "Erfolg sichern" -Percent 92

    if ($AutoCommit) {
        Commit-Success -Message $Auftrag
    }
    else {
        LogLine "AutoCommit ist nicht aktiv. Änderungen bleiben ungesichert im Arbeitsbaum."
    }

    Show-Phase -Phase "Abschluß" -Percent 100
    Write-Progress -Activity "Lokaler KI-Autopilot v5" -Completed

    LogLine "Endgültiger Git-Status:"
    LogLine (Get-GitShortStatus)

    if ($StartAppNachErfolg) {
        LogLine "App wird gestartet."
        & $StartScript
    }

    LogLine "KI-Autopilot v5 erfolgreich beendet."

    Write-Host ""
    Write-Host "AUTOPILOT ERFOLGREICH"
    Write-Host "Protokoll:"
    Write-Host $RunLog
}
catch {
    Write-Progress -Activity "Lokaler KI-Autopilot v5" -Completed
    LogLine "FEHLER: $($_.Exception.Message)"

    Write-Host ""
    Write-Host "AUTOPILOT FEHLER"
    Write-Host "Protokoll:"
    Write-Host $RunLog

    throw
}
