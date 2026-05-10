param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AiderArgs
)

$Root = "I:\KI_Legal_Project"
$Python = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$Launcher = "I:\KI_Legal_Project\Scripts\aider_local_launcher.py"

Set-Location -LiteralPath $Root
try { $PSNativeCommandUseErrorActionPreference = $false } catch {}
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}

if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "Python fehlt:"
    Write-Host $Python
    exit 1
}

if (-not (Test-Path -LiteralPath $Launcher)) {
    Write-Host "Aider-Launcher fehlt:"
    Write-Host $Launcher
    exit 1
}

$Args = @($Launcher)
$Args += $AiderArgs

& $Python @Args
exit $LASTEXITCODE
