param(
    [string] $NpmDir
)

$ErrorActionPreference = 'Stop'

$InstallDir = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.codex\codex-router'))

if (-not $NpmDir) {
    $Marker = Join-Path $InstallDir '.installed-npm-dir'
    if (Test-Path -LiteralPath $Marker) {
        $NpmDir = (Get-Content -LiteralPath $Marker -Raw).Trim()
    }
}
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

function Restore-Shim([string] $Extension) {
    $Real = Join-Path $NpmDir ("codex-real" + $Extension)
    $Wrapper = Join-Path $NpmDir ("codex" + $Extension)

    if (Test-Path -LiteralPath $Wrapper) {
        Remove-Item -LiteralPath $Wrapper -Force
    }
    if (Test-Path -LiteralPath $Real) {
        Rename-Item -LiteralPath $Real -NewName ("codex" + $Extension)
    }
}

Restore-Shim '.cmd'
Restore-Shim '.ps1'
Restore-Shim ''

Write-Host "[Codex Router] uninstalled. Original codex shims restored."
Write-Host "  npm dir     : $NpmDir"
Write-Host "  install dir : $InstallDir (left in place; delete manually if desired)"
