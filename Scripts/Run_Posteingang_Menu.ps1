param()

Set-Location -LiteralPath "I:\KI_Legal_Project"

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Root = "I:\KI_Legal_Project"
$Central = Join-Path $Root "Scripts\Run_Posteingang_Zentrale.ps1"

if (-not (Test-Path -LiteralPath $Central)) {
    Write-Host "FEHLER: Zentrale fehlt:"
    Write-Host $Central
    Set-Location -LiteralPath $Root
    exit 1
}

function Show-Menu {
    Clear-Host
    Write-Host "POSTEINGANG KI LEGAL PROJECT"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "1  Gesamtstatus"
    Write-Host "2  Produktionslauf"
    Write-Host "3  Schlußkontrolle"
    Write-Host "4  Vorzimmer-Arbeitsliste"
    Write-Host "5  Vorzimmer-Entscheidung ausführen"
    Write-Host "6  Aktenmaterial-Freigabeliste"
    Write-Host "7  Alles ausführen"
    Write-Host "0  Beenden"
    Write-Host ""
}

$ExitMenu = $false

while (-not $ExitMenu) {
    Show-Menu
    $Choice = Read-Host "Auswahl"

    try {
        switch ($Choice) {
            "1" {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion Gesamtstatus
                break
            }
            "2" {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion Produktionslauf
                break
            }
            "3" {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion Schlusskontrolle
                break
            }
            "4" {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion Arbeitsliste
                break
            }
            "5" {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion Entscheidung
                break
            }
            "6" {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion Aktenmaterial
                break
            }
            "7" {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Central -Aktion Alles
                break
            }
            "0" {
                $ExitMenu = $true
                break
            }
            default {
                Write-Host ""
                Write-Host "Ungültige Auswahl."
                Start-Sleep -Seconds 1
            }
        }
    }
    catch {
        Write-Host ""
        Write-Host "FEHLER:"
        Write-Host $_.Exception.Message
    }

    if (-not $ExitMenu) {
        Write-Host ""
        Write-Host "ENTER für Menü."
        [void][System.Console]::ReadLine()
    }
}

Set-Location -LiteralPath $Root
Write-Host ""
Write-Host "EINSTIEGSPUNKT:"
Write-Host (Get-Location)
