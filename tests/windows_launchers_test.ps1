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
$OriginalGitLog = $env:RESPECTED_GIT_LOG
$OriginalIexScript = $env:RESPECTED_IEX_SCRIPT
$OriginalIexCwd = $env:RESPECTED_IEX_CWD
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

    $IexCase = Join-Path $Root "install-iex"
    New-Item -ItemType Directory -Path $IexCase | Out-Null
    Copy-Item -LiteralPath (Join-Path $Repo "install.ps1") -Destination (Join-Path $IexCase "install.ps1")
    [IO.File]::WriteAllText(
        (Join-Path $IexCase "install.py"),
        "print('LAUNCHER_OK')`n",
        [Text.UTF8Encoding]::new($false)
    )
    $env:RESPECTED_IEX_SCRIPT = Join-Path $IexCase "install.ps1"
    $env:RESPECTED_IEX_CWD = $IexCase
    $IexCommand = 'Set-Location -LiteralPath $env:RESPECTED_IEX_CWD; Get-Content -LiteralPath $env:RESPECTED_IEX_SCRIPT -Raw | Invoke-Expression'
    $IexOutput = (& $PowerShellHost -NoProfile -Command $IexCommand 2>&1 | Out-String)
    $IexExit = $LASTEXITCODE
    if ($IexExit -ne 0 -or -not $IexOutput.Contains("LAUNCHER_OK")) {
        throw "install.ps1 pipe-to-IEX sözleşmesi başarısız: exit=$IexExit output=$IexOutput"
    }

    [IO.File]::WriteAllText(
        (Join-Path $Commands "git.cmd"),
        "@echo off`r`necho %*>`"%RESPECTED_GIT_LOG%`"`r`nexit /b 1`r`n",
        [Text.UTF8Encoding]::new($false)
    )
    foreach ($Name in @("install", "update", "uninstall")) {
        $Case = Join-Path $Root ("remote-" + $Name)
        New-Item -ItemType Directory -Path $Case | Out-Null
        Copy-Item -LiteralPath (Join-Path $Repo "$Name.ps1") -Destination (Join-Path $Case "$Name.ps1")
        $GitLog = Join-Path $Case "git-argv.txt"
        $env:RESPECTED_GIT_LOG = $GitLog
        $ExpectedVault = Join-Path $Case "Remote Vault"
        & $PowerShellHost -NoProfile -File (Join-Path $Case "$Name.ps1") -VaultPath $ExpectedVault *> $null
        if (-not (Test-Path -LiteralPath $GitLog)) {
            throw "$Name.ps1 uzak bootstrap sırasında git clone çalıştırmadı"
        }
        $GitArgv = Get-Content -LiteralPath $GitLog -Raw
        if (-not $GitArgv.Contains("https://github.com/respected0/respectedbrain.git")) {
            throw "$Name.ps1 yanlış kaynak repoyu çağırdı: $GitArgv"
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
    if ($null -eq $OriginalGitLog) {
        Remove-Item Env:RESPECTED_GIT_LOG -ErrorAction SilentlyContinue
    }
    else {
        $env:RESPECTED_GIT_LOG = $OriginalGitLog
    }
    if ($null -eq $OriginalIexScript) {
        Remove-Item Env:RESPECTED_IEX_SCRIPT -ErrorAction SilentlyContinue
    }
    else {
        $env:RESPECTED_IEX_SCRIPT = $OriginalIexScript
    }
    if ($null -eq $OriginalIexCwd) {
        Remove-Item Env:RESPECTED_IEX_CWD -ErrorAction SilentlyContinue
    }
    else {
        $env:RESPECTED_IEX_CWD = $OriginalIexCwd
    }
    Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Windows launcher tests: OK"
