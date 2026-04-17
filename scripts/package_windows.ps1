$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$distRoot = Join-Path $repoRoot "dist"
$bundleDir = Join-Path $distRoot "Snake_Game"
$bundleZipPath = Join-Path $distRoot "snake-game-windows.zip"
$shortcutInstallerSource = Join-Path $repoRoot "scripts\\install_shortcuts.ps1"
$shortcutInstallerDest = Join-Path $bundleDir "Install Shortcuts.ps1"

if (Test-Path $distRoot) {
    Remove-Item -LiteralPath $distRoot -Recurse -Force
}

python -m PyInstaller snake_game.spec --noconfirm

if (Test-Path build) {
    Remove-Item -LiteralPath build -Recurse -Force
}

if (-not (Test-Path $bundleDir)) {
    throw "Expected packaged folder not found: $bundleDir"
}

$bundleItems = Get-ChildItem -LiteralPath $bundleDir -Force
if (-not $bundleItems) {
    throw "Packaged folder is empty: $bundleDir"
}

if (-not (Test-Path $shortcutInstallerSource)) {
    throw "Shortcut installer script not found: $shortcutInstallerSource"
}

Copy-Item -LiteralPath $shortcutInstallerSource -Destination $shortcutInstallerDest -Force

Compress-Archive -LiteralPath $bundleDir -DestinationPath $bundleZipPath -Force

Remove-Item -LiteralPath $bundleDir -Recurse -Force

Write-Output "Created $bundleZipPath"
