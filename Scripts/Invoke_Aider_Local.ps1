param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AiderArgs
)

$Root = "I:\KI_Legal_Project"
$Python = "I:\KI_Legal_Project\Tools\Python312\python.exe"
$Launcher = "I:\KI_Legal_Project\Scripts\aider_local_launcher.py"

Set-Location -LiteralPath $Root

try { $PSNativeCommandUseErrorActionPreference = $false } catch {}
try { chcp.com 65001 | Out-Null } catch {}
try { [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}
try { $OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:NO_COLOR = "1"
$env:RICH_NO_COLOR = "1"
$env:PY_COLORS = "0"
$env:CLICOLOR = "0"
$env:TERM = "dumb"

if (-not (Test-Path -LiteralPath $Python)) { exit 1 }
if (-not (Test-Path -LiteralPath $Launcher)) { exit 1 }

$Args = @($Launcher)
$Args += $AiderArgs

if ($Args -notcontains "--no-auto-lint") { $Args += "--no-auto-lint" }
if ($Args -notcontains "--no-pretty") { $Args += "--no-pretty" }
if ($Args -notcontains "--no-stream") { $Args += "--no-stream" }
if ($Args -notcontains "--no-analytics") { $Args += "--no-analytics" }
if ($Args -notcontains "--no-check-update") { $Args += "--no-check-update" }

& $Python @Args
exit $LASTEXITCODE