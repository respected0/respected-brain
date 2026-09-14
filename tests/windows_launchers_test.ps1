$ErrorActionPreference = "Stop"

$Repo = Split-Path -Parent $PSScriptRoot
$PowerShellHost = (Get-Process -Id $PID).Path
$RealPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path -LiteralPath $RealPython -PathType Leaf)) {
    $Discovered = Get-Command py, python, python3 -All -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $Discovered) { throw "Windows launcher testi için çalışan Python bulunamadı" }
    $RealPython = $Discovered.Source
}

$Root = Join-Path ([IO.Path]::GetTempPath()) ("respected-launcher-test-" + [guid]::NewGuid().ToString("N"))
$Commands = Join-Path $Root "commands"
New-Item -ItemType Directory -Path $Commands | Out-Null
$OriginalPath = $env:PATH
$OriginalRealPython = $env:RESPECTED_REAL_PYTHON
try {
    [IO.File]::WriteAllText(
        (Join-Path $Commands "python.cmd"),
        "@echo off`r`necho Python was not found; run without arguments to install from the Microsoft Store.`r`nexit /b 0`r`n",
        [Text.UTF8Encoding]::new($false)
    )
    [IO.File]::WriteAllText(
        (Join-Path $Commands "python3.cmd"),
        "@echo off`r`n`"%RESPECTED_REAL_PYTHON%`" %*`r`nexit /b %errorlevel%`r`n",
        [Text.UTF8Encoding]::new($false)
    )
    $env:RESPECTED_REAL_PYTHON = $RealPython
    $env:PATH = $Commands + ";" + (Join-Path $env:SystemRoot "System32")

    foreach ($Name in @("install", "update", "uninstall")) {
        $Case = Join-Path $Root $Name
        New-Item -ItemType Directory -Path $Case | Out-Null
        Copy-Item -LiteralPath (Join-Path $Repo "$Name.ps1") -Destination (Join-Path $Case "$Name.ps1")
        [IO.File]::WriteAllText(
            (Join-Path $Case "$Name.py"),
            "import sys`nprint('LAUNCHER_OK')`nprint('ARGS')`nprint(chr(10).join(sys.argv[1:]))`n",
            [Text.UTF8Encoding]::new($false)
        )
        $ExpectedVault = Join-Path $Case "Vault With Space"
        $output = (& $PowerShellHost -NoProfile -File (Join-Path $Case "$Name.ps1") -VaultPath $ExpectedVault 2>&1 | Out-String)
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0 -or -not $output.Contains("LAUNCHER_OK")) {
            throw "$Name.ps1 Store aliasını atlayıp çalışan Python'a geçemedi: exit=$exitCode output=$output"
        }
        $OutputLines = @($output -split '\r?\n')
        if ($ExpectedVault -notin $OutputLines) {
            throw "$Name.ps1 boşluklu/özel argv değerini birebir aktarmadı: expected=$ExpectedVault output=$output"
        }
        if ($Name -eq "install") {
            if (-not $output.Contains("--python-executable") -or -not $output.Contains($RealPython)) {
                throw "install.ps1 doğrulanmış gerçek interpreter yolunu install.py'ye aktarmadı: $output"
            }
        }
    }
}
finally {
    $env:PATH = $OriginalPath
    if ($null -eq $OriginalRealPython) {
        Remove-Item Env:RESPECTED_REAL_PYTHON -ErrorAction SilentlyContinue
    }
    else {
        $env:RESPECTED_REAL_PYTHON = $OriginalRealPython
    }
    Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Windows launcher tests: OK"
