# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['soundcloud_downloader.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Kevin\\SoundCloud Downloader Project\\chromedriver_win32\\chromedriver.exe', 'chromedriver_win32'), ('C:\\Users\\Kevin\\SoundCloud Downloader Project\\ffmpeg-2023-04-30-git-e7c690a046-essentials_build\\**', 'ffmpeg-2023-04-30-git-e7c690a046-essentials_build'), ('C:\\Users\\Kevin\\SoundCloud Downloader Project\\songs', 'songs'), ('C:\\Users\\Kevin\\SoundCloud Downloader Project\\links.txt', '.'), ('C:\\Users\\Kevin\\SoundCloud Downloader Project\\window-icon.png', '.'), ('C:\\Users\\Kevin\\SoundCloud Downloader Project\\window-icon.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='soundcloud_downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Kevin\\SoundCloud Downloader Project\\window-icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='soundcloud_downloader',
)
