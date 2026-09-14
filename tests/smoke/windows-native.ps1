$ErrorActionPreference = "Stop"
$Python = $null
$Candidates = @(Get-Command py, python3, python -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source })
$Bundled = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (Test-Path -LiteralPath $Bundled -PathType Leaf) { $Candidates += $Bundled }
foreach ($Candidate in $Candidates) {
    $Probe = & $Candidate --version 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $Probe -match 'Python\s+3\.' -and $Probe -notmatch 'Microsoft Store') {
        $Python = $Candidate
        break
    }
}
if (-not $Python) { throw "Çalışan Python 3 bulunamadı; Microsoft Store aliası yeterli değildir" }
& $Python (Join-Path $PSScriptRoot "platform_smoke.py") @args
exit $LASTEXITCODE
