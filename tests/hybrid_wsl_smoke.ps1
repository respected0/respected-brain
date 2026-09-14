$ErrorActionPreference = "Stop"

$Repo = Split-Path -Parent $PSScriptRoot
$Python = "C:\Users\Furkan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    $Resolved = Get-Command py, python, python3 -All -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $Resolved) { throw "Hybrid smoke için Windows Python bulunamadı" }
    $Python = $Resolved.Source
}
$Root = Join-Path ([IO.Path]::GetTempPath()) ("respected-hybrid-smoke-" + [guid]::NewGuid().ToString("N"))
$Vault = Join-Path $Root "HybridVault"
function Convert-ToWslPath([string]$Path) {
    $Full = [IO.Path]::GetFullPath($Path)
    $Drive = $Full.Substring(0, 1).ToLowerInvariant()
    $Rest = $Full.Substring(3).Replace("\", "/")
    return "/mnt/$Drive/$Rest"
}
New-Item -ItemType Directory -Path $Root | Out-Null
try {
    & $Python (Join-Path $Repo "install.py") --defaults --vault-path $Vault --user-name Ada --user-bio Engineer --companion Echo --os-name HybridOS --environment hybrid --no-desktop-shortcut --no-install-schedule --no-install-mcp --quiet
    if ($LASTEXITCODE -ne 0) { throw "Hybrid Windows kurulumu başarısız: $LASTEXITCODE" }

    $Config = Get-Content -Raw -LiteralPath (Join-Path $Vault ".beyin\config.json") | ConvertFrom-Json
    if ($Config.platform -ne "windows-wsl") { throw "Hybrid profil windows-wsl değil: $($Config.platform)" }
    $Claude = Get-Content -Raw -LiteralPath (Join-Path $Vault ".claude\settings.json")
    if (-not $Claude.Contains("wsl.exe")) { throw "Hybrid adapter wsl.exe köprüsü üretmedi" }

    $Transcript = Join-Path $Root "transcript.jsonl"
    [IO.File]::WriteAllText(
        $Transcript,
        "{`"role`":`"user`",`"content`":`"hybrid smoke request`"}`n{`"role`":`"assistant`",`"content`":`"hybrid smoke response`"}`n",
        [Text.UTF8Encoding]::new($false)
    )
    $Model = Join-Path $Root "model.py"
    [IO.File]::WriteAllText(
        $Model,
        "print('## Bağlam\nHybrid fiziksel WSL\n\n## Önemli Konuşmalar\nWindows ve WSL köprüsü\n\n## Alınan Kararlar\nProfil doğrulandı\n\n## Öğrenilenler\nMount yazımı çalıştı\n\n## Yapılacaklar\n- Yok')`n",
        [Text.UTF8Encoding]::new($false)
    )

    $WslVault = Convert-ToWslPath $Vault
    $WslTranscript = Convert-ToWslPath $Transcript
    $WslModel = Convert-ToWslPath $Model
    $HookInput = Join-Path $Root "hook-input.json"
    $HookData = @{ session_id = "hybrid-physical-smoke"; transcript_path = $WslTranscript } | ConvertTo-Json -Compress
    [IO.File]::WriteAllText($HookInput, $HookData + "`n", [Text.UTF8Encoding]::new($false))
    $WslHookInput = Convert-ToWslPath $HookInput

    & wsl.exe -d Ubuntu -- env "BEYIN_LLM_COMMAND=python3 $WslModel" python3 "$WslVault/.beyin/engine/flush.py" --hook-input $WslHookInput --reason turn
    if ($LASTEXITCODE -ne 0) { throw "WSL flush başarısız: $LASTEXITCODE" }

    $Daily = Get-ChildItem -LiteralPath (Join-Path $Vault "daily") -Filter "*.md" | Select-Object -First 1
    if (-not $Daily) { throw "Hybrid WSL flush daily üretmedi" }
    $DailyText = Get-Content -Raw -LiteralPath $Daily.FullName
    if (-not $DailyText.Contains("Hybrid fiziksel WSL")) { throw "Hybrid daily beklenen özeti taşımıyor" }
}
finally {
    Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Hybrid WSL smoke: OK"
