Set-Location -LiteralPath "I:\KI_Legal_Project"
$ErrorActionPreference = "Stop"
try { chcp.com 65001 | Out-Null } catch {}

$Root = "I:\KI_Legal_Project"
$Python = Join-Path $Root "Tools\Python312\python.exe"
$LibraryRoot = Join-Path $Root "Tools\_ToolLibrary"
$DownloadsRoot = Join-Path $LibraryRoot "Downloads"
$WheelRoot = Join-Path $LibraryRoot "PythonWheelhouse"
$LogDir = Join-Path $Root "Windows_App\Logs"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Report = Join-Path $LogDir "RUN_UPDATE_EXTERNAL_TOOLS_LIBRARY_$Ts.txt"

New-Item -ItemType Directory -Force -Path $DownloadsRoot,$WheelRoot,$LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

function Try-WingetDownload {
    param([string]$Key,[string]$Id)

    $Dest = Join-Path $DownloadsRoot $Key
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        W "winget fehlt. Übersprungen: $Key"
        return
    }

    W "Download: $Key / $Id"
    & winget download --id $Id --exact --accept-source-agreements --accept-package-agreements --download-directory $Dest 2>&1 |
        ForEach-Object { W ([string]$_) }
}

try {
    W "UPDATE EXTERNAL TOOLS LIBRARY gestartet."
    W "Es wird nur heruntergeladen, nicht installiert."

    $Packages = @(
        @{ Key="7zip"; Id="7zip.7zip" },
        @{ Key="tesseract"; Id="UB-Mannheim.TesseractOCR" },
        @{ Key="ghostscript"; Id="ArtifexSoftware.Ghostscript" },
        @{ Key="qpdf"; Id="QPDF.qpdf" },
        @{ Key="libreoffice"; Id="TheDocumentFoundation.LibreOffice" },
        @{ Key="imagemagick"; Id="ImageMagick.ImageMagick" },
        @{ Key="exiftool"; Id="OliverBetz.ExifTool" },
        @{ Key="clamav"; Id="ClamAV.ClamAV" },
        @{ Key="java"; Id="EclipseAdoptium.Temurin.21.JRE" }
    )

    foreach ($P in $Packages) {
        Try-WingetDownload -Key $P.Key -Id $P.Id
    }

    if (Test-Path -LiteralPath $Python) {
        $Core = @("pymupdf","pillow","numpy","opencv-python","python-docx","openpyxl","duckdb","pytesseract","pyyaml")
        W "Python-Wheelhouse Download."
        & $Python -m pip download --dest $WheelRoot @Core 2>&1 |
            ForEach-Object { W ([string]$_) }
    } else {
        W "Python nicht gefunden: $Python"
    }

    W "FERTIG"
    Write-Host ""
    Write-Host "FERTIG"
    Write-Host "Report:"
    Write-Host $Report
}
catch {
    W ("FEHLER: " + $_.Exception.Message)
    Write-Host ""
    Write-Host "FEHLER"
    Write-Host $_.Exception.Message
    Write-Host "Report:"
    Write-Host $Report
}
finally {
    Set-Location -LiteralPath $Root
    Write-Host ""
    Write-Host "EINSTIEGSPUNKT:"
    Write-Host (Get-Location)
}