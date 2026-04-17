param(
    [switch]$NoDesktopShortcut,
    [switch]$NoStartMenuShortcut
)

$ErrorActionPreference = "Stop"

$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $bundleRoot "Snake Game.exe"

if (-not (Test-Path $exePath)) {
    throw "Snake Game.exe was not found next to this script. Keep this script inside the extracted Snake_Game folder."
}

$shell = New-Object -ComObject WScript.Shell
$createdShortcuts = New-Object System.Collections.Generic.List[string]

function New-Shortcut {
    param([string]$ShortcutPath)

    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $bundleRoot
    $shortcut.IconLocation = $exePath
    $shortcut.Description = "Launch Snake Game"
    $shortcut.Save()
    $createdShortcuts.Add($ShortcutPath) | Out-Null
}

if (-not $NoStartMenuShortcut) {
    $programsDir = [Environment]::GetFolderPath("Programs")
    New-Shortcut (Join-Path $programsDir "Snake Game.lnk")
}

if (-not $NoDesktopShortcut) {
    $desktopDir = [Environment]::GetFolderPath("Desktop")
    New-Shortcut (Join-Path $desktopDir "Snake Game.lnk")
}

if ($createdShortcuts.Count -eq 0) {
    Write-Output "No shortcuts were created."
    exit 0
}

foreach ($shortcutPath in $createdShortcuts) {
    Write-Output "Created shortcut: $shortcutPath"
}

Write-Output "You can now launch Snake Game from Start Menu or Desktop and pin it from there."
