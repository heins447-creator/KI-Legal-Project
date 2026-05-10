param(
    [Parameter(Mandatory=$true)]
    [string]$Auftrag,

    [string[]]$Files = @(
        "Windows_App/App/MainWindow.xaml",
        "Windows_App/App/MainWindow.xaml.cs"
    ),

    [string]$Model = "qwen2.5-coder:1.5b",

    [int]$TimeoutSeconds = 180,

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

$RunLog = Join-Path $LogDir "KI_AENDERUNGS_AGENT_V4_$Ts.txt"
$RawLog = Join-Path $LogDir "KI_AENDERUNGS_AGENT_V4_RAW_$Ts.txt"
$BackupDir = Join-Path $LogDir "BACKUP_AENDERUNGS_AGENT_V4_$Ts"

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function LogLine {
    param([string]$Text)
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $RunLog -Append
}

function Show-Phase {
    param([string]$Phase, [int]$Percent)
    Write-Progress -Activity "Lokaler KI-Änderungs-Agent v4" -Status $Phase -PercentComplete $Percent
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

function Read-ContextBlock {
    param([string]$RelativePath)

    $Full = Assert-AllowedPath $RelativePath

    if (-not (Test-Path $Full)) {
        return "DATEI FEHLT: $RelativePath"
    }

    $Content = [System.IO.File]::ReadAllText($Full)

    if ($Content.Length -gt 12000) {
        $Content = $Content.Substring(0, 12000)
    }

    return @"
===== DATEI: $RelativePath =====
$Content
===== ENDE DATEI: $RelativePath =====
"@
}

function Invoke-Ollama {
    param([string]$Prompt)

    $Body = @{
        model = $Model
        prompt = $Prompt
        stream = $false
        options = @{
            temperature = 0.0
            num_ctx = 12000
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

        Show-Phase -Phase "$Spin KI erzeugt kleine Änderungsbefehle | Laufzeit: $Elapsed s" -Percent $Percent

        if ($Elapsed % 20 -eq 0) {
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

function Extract-Actions {
    param([string]$Text)

    $StartMarker = "BEGIN_ACTIONS"
    $EndMarker = "END_ACTIONS"

    $S = $Text.IndexOf($StartMarker)
    $E = $Text.IndexOf($EndMarker)

    if ($S -ge 0 -and $E -gt $S) {
        $Json = $Text.Substring($S + $StartMarker.Length, $E - ($S + $StartMarker.Length)).Trim()
        return $Json
    }

    $First = $Text.IndexOf("[")
    $Last = $Text.LastIndexOf("]")

    if ($First -ge 0 -and $Last -gt $First) {
        return $Text.Substring($First, $Last - $First + 1).Trim()
    }

    throw "Kein ACTIONS-JSON gefunden."
}

function Count-Occurrences {
    param(
        [string]$Text,
        [string]$Search
    )

    return ([regex]::Matches($Text, [regex]::Escape($Search))).Count
}

function Replace-Once {
    param(
        [string]$Text,
        [string]$Search,
        [string]$Replace
    )

    $Index = $Text.IndexOf($Search, [System.StringComparison]::Ordinal)

    if ($Index -lt 0) {
        throw "Suchtext nicht gefunden: $Search"
    }

    return $Text.Substring(0, $Index) + $Replace + $Text.Substring($Index + $Search.Length)
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
    param([array]$Backups)

    LogLine "Rollback wird ausgeführt."

    foreach ($Item in $Backups) {
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
    LogLine "KI-Änderungs-Agent v4 gestartet."
    LogLine "Auftrag: $Auftrag"
    LogLine "Erlaubter Bereich: $AllowedRoot"

    $ContextParts = New-Object System.Collections.Generic.List[string]

    foreach ($F in $Files) {
        LogLine "Kontextdatei: $F"
        $ContextParts.Add((Read-ContextBlock $F))
    }

    $Context = $ContextParts -join "`n`n"

    $Prompt = @"
Du bist ein lokaler KI-Programmierer für eine Windows-WPF-App.

Du darfst ausschließlich kleine Änderungsbefehle ausgeben.

Arbeitsregeln:
- Arbeite ausschließlich unter Windows_App.
- Keine Cloud.
- Keine GitHub-Verbindung.
- Keine externen Repositories.
- Keine Zugangsdaten.
- Keine Änderungen an AnythingLLM_Storage.
- Gib keine Erklärung aus.
- Gib keine Markdown-Codeblöcke aus.
- Gib nur BEGIN_ACTIONS bis END_ACTIONS aus.
- Verwende nur exakte Suchtexte, die im Dateistand sichtbar vorhanden sind.
- Wenn etwas ersetzt wird, muß der Suchtext eindeutig sein.

Erlaubte Aktionen:
1. replace_once
   Felder:
   type, path, search, replace

2. insert_after_once
   Felder:
   type, path, after, insert

Antwortformat:
BEGIN_ACTIONS
[
  {
    "type": "replace_once",
    "path": "Windows_App/App/MainWindow.xaml",
    "search": "Title=\"KI Legal Project\"",
    "replace": "Title=\"KI Legal Project Test\""
  }
]
END_ACTIONS

AUFTRAG:
$Auftrag

AKTUELLER DATEISTAND:
$Context
"@

    Show-Phase -Phase "Phase 2/5: KI erzeugt Änderungsbefehle" -Percent 15

    $Response = Invoke-Ollama -Prompt $Prompt
    $Response | Set-Content -LiteralPath $RawLog -Encoding UTF8

    Show-Phase -Phase "Phase 3/5: Änderungsbefehle prüfen" -Percent 65

    $Json = Extract-Actions $Response
    $Actions = $Json | ConvertFrom-Json

    if ($null -eq $Actions) {
        throw "Keine Aktionen erhalten."
    }

    if ($Actions -isnot [System.Array]) {
        $Actions = @($Actions)
    }

    $Backups = New-Object System.Collections.Generic.List[object]
    $Touched = @{}

    Show-Phase -Phase "Phase 4/5: Änderungen anwenden" -Percent 78

    foreach ($Action in $Actions) {
        $Type = [string]$Action.type
        $Rel = [string]$Action.path
        $Target = Assert-AllowedPath $Rel

        if (-not (Test-Path $Target)) {
            throw "Zieldatei fehlt: $Rel"
        }

        if (-not $Touched.ContainsKey($Target)) {
            $SafeName = ($Rel -replace "[:\\\/]", "_")
            $BackupPath = Join-Path $BackupDir $SafeName

            Copy-Item -LiteralPath $Target -Destination $BackupPath -Force

            $Backups.Add([pscustomobject]@{
                TargetPath = $Target
                BackupPath = $BackupPath
                ExistedBefore = $true
            })

            $Touched[$Target] = $true
        }

        $Text = [System.IO.File]::ReadAllText($Target)

        if ($Type -eq "replace_once") {
            $Search = [string]$Action.search
            $Replace = [string]$Action.replace

            $Count = Count-Occurrences -Text $Text -Search $Search

            if ($Count -ne 1) {
                throw "replace_once erwartet genau 1 Treffer, gefunden: $Count. Suchtext: $Search"
            }

            $Text = Replace-Once -Text $Text -Search $Search -Replace $Replace
            [System.IO.File]::WriteAllText($Target, $Text, $Utf8NoBom)
            LogLine "replace_once angewendet: $Rel"
        }
        elseif ($Type -eq "insert_after_once") {
            $After = [string]$Action.after
            $Insert = [string]$Action.insert

            $Count = Count-Occurrences -Text $Text -Search $After

            if ($Count -ne 1) {
                throw "insert_after_once erwartet genau 1 Treffer, gefunden: $Count. Suchtext: $After"
            }

            $Text = Replace-Once -Text $Text -Search $After -Replace ($After + $Insert)
            [System.IO.File]::WriteAllText($Target, $Text, $Utf8NoBom)
            LogLine "insert_after_once angewendet: $Rel"
        }
        else {
            throw "Unbekannte Aktion: $Type"
        }
    }

    if (-not $NoBuild) {
        Show-Phase -Phase "Phase 5/5: Build prüfen" -Percent 90

        try {
            Build-App
        }
        catch {
            LogLine "Buildfehler nach KI-Änderung: $($_.Exception.Message)"
            Restore-Backups -Backups $Backups
            Build-App
            throw "KI-Änderung wurde wegen Buildfehler zurückgerollt."
        }
    }

    Show-Phase -Phase "Fertig" -Percent 100
    Write-Progress -Activity "Lokaler KI-Änderungs-Agent v4" -Completed

    LogLine "Git-Status:"
    git -C $Root status --short 2>&1 | Tee-Object -FilePath $RunLog -Append

    LogLine "KI-Änderungs-Agent v4 beendet."

    Write-Host ""
    Write-Host "Fertig. Protokoll:"
    Write-Host $RunLog
    Write-Host ""
    Write-Host "Rohantwort:"
    Write-Host $RawLog
}
catch {
    Write-Progress -Activity "Lokaler KI-Änderungs-Agent v4" -Completed
    LogLine "FEHLER: $($_.Exception.Message)"
    throw
}
