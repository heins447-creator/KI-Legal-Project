param()

Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Root = "I:\KI_Legal_Project"
$Central = Join-Path $Root "Scripts\Run_Posteingang_Zentrale.ps1"
$Failed = $false

function Run-Action {
    param([string]$Aktion)

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion $Aktion
    if ($LASTEXITCODE -ne 0) {
        throw "Aktion fehlgeschlagen: $Aktion"
    }
}

try {
    while ($true) {
        Clear-Host
        Write-Host "POSTEINGANG MENUE"
        Write-Host "================="
        Write-Host ""
        Write-Host "1  Gesamtstatus"
        Write-Host "2  Produktionslauf"
        Write-Host "3  Schlußkontrolle"
        Write-Host "4  Vorzimmer-Arbeitsliste"
        Write-Host "5  Vorzimmer-Entscheidung"
        Write-Host "6  Aktenmaterial-Freigabeliste"
        Write-Host "7  Vorzimmer-Kommunikationsparameter"
        Write-Host "8  Alles ausführen"
        Write-Host "0  Beenden"
        Write-Host ""

        $Choice = Read-Host "Auswahl"

        switch ($Choice) {
            "1" { Run-Action "Gesamtstatus"; Read-Host "Enter" }
            "2" { Run-Action "Produktionslauf"; Read-Host "Enter" }
            "3" { Run-Action "Schlusskontrolle"; Read-Host "Enter" }
            "4" { Run-Action "Arbeitsliste"; Read-Host "Enter" }
            "5" { Run-Action "Entscheidung"; Read-Host "Enter" }
            "6" { Run-Action "Aktenmaterial"; Read-Host "Enter" }
            "7" { Run-Action "Kommunikation"; Read-Host "Enter" }
            "8" { Run-Action "Alles"; Read-Host "Enter" }
            "0" { break }
            default { Write-Host "Ungültige Auswahl."; Start-Sleep -Seconds 1 }
        }
    }
}
catch {
    $Failed = $true
    Write-Host ""
    Write-Host "FEHLER"
    Write-Host $_.Exception.Message
}
finally {
    Set-Location -LiteralPath $Root

    Write-Host ""
    Write-Host "EINSTIEGSPUNKT:"
    Write-Host (Get-Location)

    if ($Failed) {
        Write-Host "Fehlerbericht prüfen."
        exit 1
    } else {
        Write-Host "Menü beendet."
        exit 0
    }
}
