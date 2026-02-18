# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Neptune.
Bundles the Python backend + built frontend into a distributable folder.

Usage:
    pyinstaller neptune.spec
"""

import os, sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect torchvision data (pretrained model configs, etc.)
torch_data = collect_data_files("torchvision")
torch_hidden = collect_submodules("torchvision.models")

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        # Include the built React frontend
        ("frontend/dist", "frontend/dist"),
        # Include backend Python source
        ("backend", "backend"),
    ] + torch_data,
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "backend",
        "backend.main",
        "backend.model",
        "backend.indexer",
        "backend.version",
        "backend.updater",
        "pystray",
        "PIL",
    ] + torch_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude CUDA to keep the bundle small (CPU inference only)
        "torch.cuda",
        "torch.distributed",
        "torch.testing",
        "torch.utils.bottleneck",
        "torch.utils.tensorboard",
        "tensorboard",
        "matplotlib",
        "scipy",
        "pandas",
        "jupyter",
        "notebook",
        "IPython",
        "tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Neptune",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — runs in background with tray icon
    icon=None,      # TODO: Add icon file later
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Neptune",
)
