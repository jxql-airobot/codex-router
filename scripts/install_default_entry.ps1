param(
    [string] $NpmDir
)

$ErrorActionPreference = 'Stop'

$Source = Split-Path $PSScriptRoot -Parent
$InstallDir = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.codex\codex-router'))

if (-not $NpmDir) {
    $NpmDir = (& npm prefix -g 2>$null)
}
if (-not $NpmDir) {
    $NpmDir = Join-Path $env:APPDATA 'npm'
}
$NpmDir = [System.IO.Path]::GetFullPath($NpmDir)

if (-not (Test-Path -LiteralPath $NpmDir -PathType Container)) {
    throw "npm global bin directory not found: $NpmDir"
}
if ($NpmDir -eq [System.IO.Path]::GetPathRoot($NpmDir)) {
    throw "Refusing to use a filesystem root as npm dir: $NpmDir"
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

$RuntimeFiles = @(
    'codex-auto.py',
    'classifier.py',
    'model_selector.py',
    'config_loader.py',
    'config.yaml',
    'router.py',
    'git_lifecycle.py',
    'rag_query.py',
    'requirements.txt'
)
foreach ($File in $RuntimeFiles) {
    Copy-Item -LiteralPath (Join-Path $Source $File) `
        -Destination (Join-Path $InstallDir $File) -Force
}

$LauncherDest = Join-Path $InstallDir 'launcher'
if (-not $LauncherDest.StartsWith($InstallDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to delete unexpected launcher path: $LauncherDest"
}
if (Test-Path -LiteralPath $LauncherDest) {
    Remove-Item -LiteralPath $LauncherDest -Recurse -Force
}
Copy-Item -LiteralPath (Join-Path $Source 'launcher') -Destination $LauncherDest -Recurse

$AgentsDest = Join-Path $InstallDir 'agents'
if (-not $AgentsDest.StartsWith($InstallDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to delete unexpected agents path: $AgentsDest"
}
if (Test-Path -LiteralPath $AgentsDest) {
    Remove-Item -LiteralPath $AgentsDest -Recurse -Force
}
Copy-Item -LiteralPath (Join-Path $Source 'agents') -Destination $AgentsDest -Recurse

$MemoryDest = Join-Path $InstallDir 'memory'
if (-not $MemoryDest.StartsWith($InstallDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to delete unexpected memory path: $MemoryDest"
}
if (Test-Path -LiteralPath $MemoryDest) {
    Remove-Item -LiteralPath $MemoryDest -Recurse -Force
}
Copy-Item -LiteralPath (Join-Path $Source 'memory') -Destination $MemoryDest -Recurse

foreach ($Dir in @('git_manager', 'task_manager', 'report', 'vector_store', 'knowledge', 'rag')) {
    $ExtraDest = Join-Path $InstallDir $Dir
    if (-not $ExtraDest.StartsWith($InstallDir, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to delete unexpected path: $ExtraDest"
    }
    if (Test-Path -LiteralPath $ExtraDest) {
        Remove-Item -LiteralPath $ExtraDest -Recurse -Force
    }
    Copy-Item -LiteralPath (Join-Path $Source $Dir) -Destination $ExtraDest -Recurse
}

function Backup-Shim([string] $Extension) {
    $Real = Join-Path $NpmDir ("codex-real" + $Extension)
    $Wrapper = Join-Path $NpmDir ("codex" + $Extension)

    if (Test-Path -LiteralPath $Real) {
        return
    }
    if (Test-Path -LiteralPath $Wrapper) {
        Rename-Item -LiteralPath $Wrapper -NewName ("codex-real" + $Extension)
    }
}

Backup-Shim '.cmd'
Backup-Shim '.ps1'
Backup-Shim ''

$PythonPath = (Join-Path $InstallDir 'codex-auto.py')
$UnixPath = $PythonPath.Replace('\', '/')

$CmdContent = @"
@echo off
python "$PythonPath" --entry %*
"@
[System.IO.File]::WriteAllText(
    (Join-Path $NpmDir 'codex.cmd'),
    $CmdContent,
    [System.Text.Encoding]::ASCII
)

$Ps1Content = @"
param([Parameter(ValueFromRemainingArguments = `$true)][string[]] `$CodexArgs)
& python '$PythonPath' --entry @CodexArgs
exit `$LASTEXITCODE
"@
[System.IO.File]::WriteAllText(
    (Join-Path $NpmDir 'codex.ps1'),
    $Ps1Content,
    (New-Object System.Text.UTF8Encoding($false))
)

$ShContent = @"
#!/bin/sh
exec python "$UnixPath" --entry "`$@"
"@
[System.IO.File]::WriteAllText(
    (Join-Path $NpmDir 'codex'),
    $ShContent,
    (New-Object System.Text.UTF8Encoding($false))
)

[System.IO.File]::WriteAllText(
    (Join-Path $InstallDir '.installed-npm-dir'),
    $NpmDir + [Environment]::NewLine,
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "[Codex Router] installed."
Write-Host "  source      : $Source"
Write-Host "  install dir : $InstallDir"
Write-Host "  npm dir     : $NpmDir"
Write-Host "  real binary : codex-real"
