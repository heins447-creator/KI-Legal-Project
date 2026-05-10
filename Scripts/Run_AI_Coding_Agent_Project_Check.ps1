param(
    [string]$Root = "I:\KI_Legal_Project"
)

Set-Location -LiteralPath $Root
try { $PSNativeCommandUseErrorActionPreference = $false } catch {}
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

$Python = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$LogDir = Join-Path $Root "Windows_App\Logs\Agentenlaeufe"
$Ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$Report = Join-Path $LogDir "PROJECT_CHECK_$Ts.txt"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function W {
    param([string]$Text = "")
    $Line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    $Line | Tee-Object -FilePath $Report -Append
}

try {
    W "PROJECT CHECK gestartet."

    $Csproj = Join-Path $Root "Windows_App\App\KI_Legal_WindowsApp.csproj"

    if (Test-Path -LiteralPath $Csproj) {
        W "dotnet build"
        dotnet build $Csproj 2>&1 | Tee-Object -FilePath $Report -Append
        if ($LASTEXITCODE -ne 0) { throw "dotnet build fehlgeschlagen." }
    }

    $Changed = @()
    $Changed += git -C $Root diff --name-only HEAD 2>&1
    $Changed += git -C $Root ls-files --others --exclude-standard 2>&1
    $Changed = $Changed | Where-Object { $_ -and $_.Trim() } | Sort-Object -Unique

    foreach ($Rel in $Changed) {
        if ($Rel.ToLowerInvariant().EndsWith(".ps1")) {
            $Full = Join-Path $Root $Rel
            $Tokens = $null
            $Errors = $null
            [System.Management.Automation.Language.Parser]::ParseFile($Full, [ref]$Tokens, [ref]$Errors) | Out-Null
            if ($Errors -and $Errors.Count -gt 0) {
                foreach ($Err in $Errors) { W ("PS-FEHLER: " + $Rel + " | " + $Err.Message) }
                throw "PowerShell-Syntaxfehler."
            }
        }

        if ($Rel.ToLowerInvariant().EndsWith(".py")) {
            $Full = Join-Path $Root $Rel
            & $Python -m py_compile $Full 2>&1 | Tee-Object -FilePath $Report -Append
            if ($LASTEXITCODE -ne 0) { throw "Python-Syntaxfehler: $Rel" }
        }
    }

    git -C $Root status --short 2>&1 | Tee-Object -FilePath $Report -Append

    Write-Host "PROJECT_CHECK_OK"
    Write-Host "Report:"
    Write-Host $Report
    exit 0
}
catch {
    W ("FEHLER: " + $_.Exception.Message)
    Write-Host "PROJECT_CHECK_FEHLER"
    Write-Host $_.Exception.Message
    Write-Host "Report:"
    Write-Host $Report
    exit 1
}
finally {
    Set-Location -LiteralPath $Root
}
