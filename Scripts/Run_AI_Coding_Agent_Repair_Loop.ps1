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
$LogRoot = Join-Path $Root "Windows_App\Logs\Agentenlaeufe"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$RunDir = Join-Path $LogRoot "AI_AGENT_RUN_$Ts"
$Report = Join-Path $RunDir "AI_AGENT_REPAIR_LOOP_$Ts.txt"
$Success = $false
$BaseCommit = ""

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
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

    if (-not (Test-Path -LiteralPath $AiderInvoker)) { throw "Aider-Invoker fehlt." }
    if (-not (Test-Path -LiteralPath $TaskFile)) { throw "Auftragsdatei fehlt." }
    if (-not (Test-Path -LiteralPath $ProjectCheck)) { throw "Projektprüfskript fehlt." }

    if ((-not $env:DEEPSEEK_API_KEY) -or ($env:DEEPSEEK_API_KEY -eq "DEIN_KEY")) {
        throw "DEEPSEEK_API_KEY fehlt oder ist nur Platzhalter."
    }

    $GitStatusBefore = git -C $Root status --short 2>&1

    if ($GitStatusBefore -and -not $AllowDirty) {
        W "Git-Status ist nicht sauber:"
        $GitStatusBefore | Tee-Object -FilePath $Report -Append
        throw "Repository ist nicht sauber. Erst committen oder mit -AllowDirty ausdrücklich erlauben."
    }

    $BaseCommit = (git -C $Root rev-parse HEAD).Trim()
    W "Basis-Commit: $BaseCommit"

    $TaskName = [System.IO.Path]::GetFileNameWithoutExtension($TaskFile)
    $SafeTaskName = ($TaskName -replace '[^a-zA-Z0-9_\-]', '_')
    $BranchName = "agent/$SafeTaskName-$Ts"

    git -C $Root checkout -b $BranchName 2>&1 | Tee-Object -FilePath $Report -Append
    if ($LASTEXITCODE -ne 0) { throw "Git-Arbeitszweig konnte nicht angelegt werden." }

    $LastError = ""

    for ($Round = 0; $Round -le $MaxRepairRounds; $Round++) {
        if ($Round -eq 0) {
            $Prompt = Join-Path $RunDir "agent_prompt_initial.md"
            New-AgentPrompt -SourceTask $TaskFile -PromptPath $Prompt -Mode "Grundgerüst"
        } else {
            $Prompt = Join-Path $RunDir ("agent_prompt_repair_{0}.md" -f $Round)
            New-AgentPrompt -SourceTask $TaskFile -PromptPath $Prompt -Mode "Reparatur" -ErrorText $LastError
        }

        powershell.exe -NoProfile -ExecutionPolicy Bypass -File $AiderInvoker --model $CheapModel --message-file $Prompt --yes --no-auto-commits --no-dirty-commits 2>&1 | Tee-Object -FilePath $Report -Append

        if ($LASTEXITCODE -ne 0) {
            $LastError = "Aider-Lauf fehlgeschlagen. Siehe Report."
            continue
        }

        powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ProjectCheck -Root $Root 2>&1 | Tee-Object -FilePath $Report -Append

        if ($LASTEXITCODE -eq 0) {
            $Success = $true
            break
        } else {
            $LastError = "Projektprüfung fehlgeschlagen. Siehe Report."
        }
    }

    if (-not $Success) {
        throw "Agent konnte den Auftrag nicht erfolgreich abschließen."
    }

    git -C $Root add -A 2>&1 | Tee-Object -FilePath $Report -Append
    if ($LASTEXITCODE -ne 0) { throw "Git add fehlgeschlagen." }

    git -C $Root diff --cached --quiet
    $DiffCode = $LASTEXITCODE

    if ($DiffCode -eq 1) {
        git -C $Root commit -m "AI-Agent: $TaskName" 2>&1 | Tee-Object -FilePath $Report -Append
        if ($LASTEXITCODE -ne 0) { throw "Git commit fehlgeschlagen." }
    }

    git -C $Root status --short 2>&1 | Tee-Object -FilePath $Report -Append

    Write-Host ""
    Write-Host "FERTIG"
    Write-Host "Report:"
    Write-Host $Report
    Write-Host "Arbeitszweig:"
    Write-Host $BranchName
    exit 0
}
catch {
    W ("FEHLER: " + $_.Exception.Message)

    if ($RollbackOnFail -and $BaseCommit) {
        git -C $Root reset --hard $BaseCommit 2>&1 | Tee-Object -FilePath $Report -Append
        if ($CleanUntrackedOnFail) {
            git -C $Root clean -fd 2>&1 | Tee-Object -FilePath $Report -Append
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
