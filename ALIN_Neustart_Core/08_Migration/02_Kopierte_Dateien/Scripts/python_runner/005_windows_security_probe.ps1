param(
    [Parameter(Mandatory=$true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"

try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
} catch {}

$result = [ordered]@{
    path = $Path
    exists = (Test-Path -LiteralPath $Path)
    defender_available = $false
    defender_scan_started = $false
    defender_error = ""
    authenticode_available = $false
    authenticode_status = ""
    authenticode_status_message = ""
    signer_subject = ""
    signer_issuer = ""
    signer_thumbprint = ""
    signer_not_before = ""
    signer_not_after = ""
    authenticode_error = ""
}

try {
    $cmd = Get-Command Start-MpScan -ErrorAction SilentlyContinue
    if ($cmd) {
        $result["defender_available"] = $true
        Start-MpScan -ScanType CustomScan -ScanPath $Path -ErrorAction Stop | Out-Null
        $result["defender_scan_started"] = $true
    }
} catch {
    $result["defender_error"] = $_.Exception.Message
}

try {
    $cmd2 = Get-Command Get-AuthenticodeSignature -ErrorAction SilentlyContinue
    if ($cmd2) {
        $result["authenticode_available"] = $true
        $sig = Get-AuthenticodeSignature -LiteralPath $Path -ErrorAction Stop

        $result["authenticode_status"] = [string]$sig.Status
        $result["authenticode_status_message"] = [string]$sig.StatusMessage

        if ($sig.SignerCertificate) {
            $result["signer_subject"] = [string]$sig.SignerCertificate.Subject
            $result["signer_issuer"] = [string]$sig.SignerCertificate.Issuer
            $result["signer_thumbprint"] = [string]$sig.SignerCertificate.Thumbprint
            $result["signer_not_before"] = [string]$sig.SignerCertificate.NotBefore
            $result["signer_not_after"] = [string]$sig.SignerCertificate.NotAfter
        }
    }
} catch {
    $result["authenticode_error"] = $_.Exception.Message
}

$result | ConvertTo-Json -Depth 6 -Compress
