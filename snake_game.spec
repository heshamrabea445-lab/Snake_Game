# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path.cwd()
icon_path = project_root / "images" / "snake_icon.ico"
datas = [
    (str(project_root / "audio"), "audio"),
    (str(project_root / "images"), "images"),
    (str(project_root / "sprites"), "sprites"),
]


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Snake Game",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Snake_Game",
)
