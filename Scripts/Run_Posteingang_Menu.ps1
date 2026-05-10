param(
    [string]$CaseTemplate = "TEMPLATE_SE_ARBEITSRECHT"
)

Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Root = "I:\KI_Legal_Project"
$Zentrale = Join-Path $Root "Scripts\Run_Posteingang_Zentrale.ps1"

function Run-Zentrale {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Aktion
    )

    if (-not (Test-Path -LiteralPath $Zentrale)) {
        throw "Posteingang-Zentrale fehlt: $Zentrale"
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Zentrale -Aktion $Aktion -CaseTemplate $CaseTemplate
}

$ExitRequested = $false

while (-not $ExitRequested) {
    Set-Location -LiteralPath $Root

    Write-Host ""
    Write-Host "POSTEINGANG ZENTRALE"
    Write-Host "===================="
    Write-Host ""
    Write-Host "1  Gesamtstatus"
    Write-Host "2  Produktionslauf"
    Write-Host "3  Vorzimmer-Arbeitsliste"
    Write-Host "4  Vorzimmer-Entscheidung"
    Write-Host "5  Betriebsstatus"
    Write-Host "0  Beenden"
    Write-Host ""

    $Choice = Read-Host "Auswahl"

    try {
        switch ($Choice) {
            "1" { Run-Zentrale -Aktion "Gesamtstatus" }
            "2" { Run-Zentrale -Aktion "Produktionslauf" }
            "3" { Run-Zentrale -Aktion "Arbeitsliste" }
            "4" { Run-Zentrale -Aktion "Entscheidung" }
            "5" { Run-Zentrale -Aktion "Status" }
            "0" { $ExitRequested = $true }
            default { Write-Host "Ungültige Auswahl." }
        }
    }
    catch {
        Write-Host ""
        Write-Host "FEHLER"
        Write-Host $_.Exception.Message
    }

    if (-not $ExitRequested) {
        Write-Host ""
        Read-Host "Enter für Menü"
    }
}

Set-Location -LiteralPath $Root
Write-Host ""
Write-Host "EINSTIEGSPUNKT:"
Write-Host (Get-Location)
