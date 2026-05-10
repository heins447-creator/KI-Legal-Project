param(
    [string]$TaskFile = "I:\KI_Legal_Project\Projektplanung\Auftraege\001_QUELLENBETREUER_FACHANWALTSRASTER_V1.md",
    [string]$CheapModel = "deepseek/deepseek-chat",
    [int]$MaxRepairRounds = 3,
    [bool]$RollbackOnFail = $true,
    [bool]$CleanUntrackedOnFail = $false,
    [switch]$AllowDirty
)

Set-Location -LiteralPath "I:\KI_Legal_Project"

try { $PSNativeCommandUseErrorActionPreference = $false } catch {}
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Root = "I:\KI_Legal_Project"
$AiderInvoker = Join-Path $Root "Scripts\Invoke_Aider_Local.ps1"
$ProjectCheck = Join-Path $Root "Scripts\Run_AI_Coding_Agent_Project_Check.ps1"
$TmpDir = Join-Path $Root "Tools\tmp"
$LogRoot = Join-Path $Root "Windows_App\Logs\Agentenlaeufe"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$RunDir = Join-Path $LogRoot "AI_AGENT_RUN_$Ts"
$Report = Join-Path $RunDir "AI_AGENT_REPAIR_LOOP_$Ts.txt"
$Success = $false
$BaseCommit = ""

New-Item -ItemType Directory -Force -Path $RunDir,$TmpDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

function Q {
    param([string]$Text)
    if ($null -eq $Text) { return '""' }
    return '"' + ($Text -replace '"','\"') + '"'
}

function Run-Cmd {
    param(
        [Parameter(Mandatory=$true)][string]$Command,
        [string]$Name = "cmd"
    )

    W ("BEFEHL: " + $Command)

    $OutFile = Join-Path $TmpDir ("out_" + $Name + "_" + [guid]::NewGuid().ToString("N") + ".txt")
    $ErrFile = Join-Path $TmpDir ("err_" + $Name + "_" + [guid]::NewGuid().ToString("N") + ".txt")
    $CmdLine = "/d /c " + $Command + " 1>" + (Q $OutFile) + " 2>" + (Q $ErrFile)

    $P = Start-Process -FilePath "cmd.exe" -ArgumentList $CmdLine -Wait -PassThru -NoNewWindow

    $Out = ""
    $Err = ""

    if (Test-Path -LiteralPath $OutFile) {
        $Out = Get-Content -LiteralPath $OutFile -Raw -ErrorAction SilentlyContinue
    }

    if (Test-Path -LiteralPath $ErrFile) {
        $Err = Get-Content -LiteralPath $ErrFile -Raw -ErrorAction SilentlyContinue
    }

    if ($Out) {
        $Out -split "`r?`n" | ForEach-Object { if ($_ -ne "") { W $_ } }
    }

    if ($Err) {
        $Err -split "`r?`n" | ForEach-Object { if ($_ -ne "") { W $_ } }
    }

    Remove-Item -LiteralPath $OutFile,$ErrFile -Force -ErrorAction SilentlyContinue

    return [pscustomobject]@{
        ExitCode = $P.ExitCode
        Output = (($Out + "`n" + $Err) | Out-String)
    }
}

function New-AgentPrompt {
    param(
        [string]$SourceTask,
        [string]$PromptPath,
        [string]$Mode,
        [string]$ErrorText = ""
    )

    $TaskText = Get-Content -LiteralPath $SourceTask -Raw

    $Prefix = @"
# KI_Legal_Project Coding-Agent Auftrag

Modus: $Mode

Arbeite ausschließlich im Projektordner:

I:\KI_Legal_Project

AGENTS.md ist verbindlich.

## Harte Grenzen

Keine echten Mandantendaten verwenden.
Keine freie Internetrecherche.
Keine API-Schlüssel schreiben.
Keine Änderungen außerhalb des Projektordners.
Keine rechtliche Endbewertung.
Keine Türschwelle programmieren, solange Quellenbetreuer und Fachanwaltsraster nicht als Grundlage stehen.

## Lieferpflicht

Erzeuge oder korrigiere genau den beauftragten Baustein.

Jeder erfolgreiche Baustein muß enthalten, soweit passend:

- Migration
- Python-Läufer
- Python-Prüfdatei
- PowerShell-Starter
- Konfiguration
- Dokumentation
- Bericht
- wiederholbarer Test

## Technische Pflicht

Alle Python-Dateien müssen syntaktisch gültig sein.
Alle PowerShell-Dateien müssen syntaktisch gültig sein.
Der .NET-Build darf nicht brechen.
Bei Unsicherheit: konservativ bauen, keine freie Architekturentscheidung.

"@

    if ($ErrorText) {
        $Prefix += @"

## Vorheriger Fehler

$ErrorText

"@
    }

    ($Prefix + "`n`n# Ursprünglicher Auftrag`n`n" + $TaskText) | Set-Content -LiteralPath $PromptPath -Encoding UTF8
}

try {
    W "AI CODING AGENT REPAIR LOOP gestartet."
    W "Root: $Root"
    W "TaskFile: $TaskFile"
    W "CheapModel: $CheapModel"
    W "MaxRepairRounds: $MaxRepairRounds"

    if (-not (Test-Path -LiteralPath $AiderInvoker)) { throw "Aider-Invoker fehlt: $AiderInvoker" }
    if (-not (Test-Path -LiteralPath $TaskFile)) { throw "Auftragsdatei fehlt: $TaskFile" }
    if (-not (Test-Path -LiteralPath $ProjectCheck)) { throw "Projektprüfskript fehlt: $ProjectCheck" }

    if ((-not $env:DEEPSEEK_API_KEY) -or ($env:DEEPSEEK_API_KEY -eq "DEIN_KEY") -or ($env:DEEPSEEK_API_KEY -eq "ECHTER_DEEPSEEK_API_KEY")) {
        throw "DEEPSEEK_API_KEY fehlt oder ist nur Platzhalter."
    }

    $StatusBefore = Run-Cmd -Name "statusbefore" -Command ("git -C " + (Q $Root) + " status --short")
    if ($StatusBefore.ExitCode -ne 0) { throw "Git-Status konnte nicht gelesen werden." }

    $StatusText = ""
    if ($StatusBefore.Output) { $StatusText = ([string]$StatusBefore.Output).Trim() }

    if ($StatusText -and -not $AllowDirty) {
        W "Git-Status ist nicht sauber:"
        W $StatusText
        throw "Repository ist nicht sauber. Erst committen oder mit -AllowDirty ausdrücklich erlauben."
    }

    $Head = Run-Cmd -Name "head" -Command ("git -C " + (Q $Root) + " rev-parse HEAD")
    if ($Head.ExitCode -ne 0) { throw "Basis-Commit konnte nicht gelesen werden." }

    $BaseCommit = ""
    if ($Head.Output) { $BaseCommit = ([string]$Head.Output).Trim() }
    W "Basis-Commit: $BaseCommit"

    $TaskName = [System.IO.Path]::GetFileNameWithoutExtension($TaskFile)
    $SafeTaskName = ($TaskName -replace '[^a-zA-Z0-9_\-]', '_')
    $BranchName = "agent/$SafeTaskName-$Ts"

    $Checkout = Run-Cmd -Name "checkout" -Command ("git -C " + (Q $Root) + " checkout -b " + (Q $BranchName))
    if ($Checkout.ExitCode -ne 0) { throw "Git-Arbeitszweig konnte nicht angelegt werden." }

    $LastError = ""

    for ($Round = 0; $Round -le $MaxRepairRounds; $Round++) {
        if ($Round -eq 0) {
            W "Runde 0: Grundgerüst erstellen"
            $Prompt = Join-Path $RunDir "agent_prompt_initial.md"
            New-AgentPrompt -SourceTask $TaskFile -PromptPath $Prompt -Mode "Grundgerüst"
        } else {
            W "Reparaturrunde $Round"
            $Prompt = Join-Path $RunDir ("agent_prompt_repair_{0}.md" -f $Round)
            New-AgentPrompt -SourceTask $TaskFile -PromptPath $Prompt -Mode "Reparatur" -ErrorText $LastError
        }

        $AiderCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File " + (Q $AiderInvoker) +
            " --model " + (Q $CheapModel) +
            " --message-file " + (Q $Prompt) +
            " --yes --no-auto-commits --no-dirty-commits"

        $Aider = Run-Cmd -Name ("aider_" + $Round) -Command $AiderCmd

        if ($Aider.ExitCode -ne 0) {
            $LastError = $Aider.Output
            W "Aider-Lauf fehlgeschlagen."
            continue
        }

        $CheckCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File " + (Q $ProjectCheck) + " -Root " + (Q $Root)
        $Check = Run-Cmd -Name ("check_" + $Round) -Command $CheckCmd

        if ($Check.ExitCode -eq 0) {
            $Success = $true
            W "Projektprüfung erfolgreich."
            break
        } else {
            $LastError = $Check.Output
            W "Projektprüfung fehlgeschlagen."
        }
    }

    if (-not $Success) {
        throw "Agent konnte den Auftrag nicht erfolgreich abschließen."
    }

    $Add = Run-Cmd -Name "add" -Command ("git -C " + (Q $Root) + " add -A")
    if ($Add.ExitCode -ne 0) { throw "Git add fehlgeschlagen." }

    $Diff = Run-Cmd -Name "diff" -Command ("git -C " + (Q $Root) + " diff --cached --quiet")

    if ($Diff.ExitCode -eq 1) {
        $Commit = Run-Cmd -Name "commit" -Command ("git -C " + (Q $Root) + " commit -m " + (Q ("AI-Agent: " + $TaskName)))
        if ($Commit.ExitCode -ne 0) { throw "Git commit fehlgeschlagen." }
    } elseif ($Diff.ExitCode -ne 0) {
        throw "Git diff Prüfung fehlgeschlagen."
    }

    $FinalStatus = Run-Cmd -Name "finalstatus" -Command ("git -C " + (Q $Root) + " status --short")

    W "AI CODING AGENT REPAIR LOOP abgeschlossen."

    Write-Host ""
    Write-Host "FERTIG"
    Write-Host "Report:"
    Write-Host $Report
    Write-Host ""
    Write-Host "Arbeitszweig:"
    Write-Host $BranchName
    exit 0
}
catch {
    W ("FEHLER: " + $_.Exception.Message)

    if ($RollbackOnFail -and $BaseCommit) {
        W "Rollback wird ausgeführt."
        $Reset = Run-Cmd -Name "reset" -Command ("git -C " + (Q $Root) + " reset --hard " + (Q $BaseCommit))
        if ($CleanUntrackedOnFail) {
            $Clean = Run-Cmd -Name "clean" -Command ("git -C " + (Q $Root) + " clean -fd")
        }
    }

    Write-Host ""
    Write-Host "FEHLER"
    Write-Host $_.Exception.Message
    Write-Host "Report:"
    Write-Host $Report
    exit 1
}
finally {
    Set-Location -LiteralPath $Root
}
