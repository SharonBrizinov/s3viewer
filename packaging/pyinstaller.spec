# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['src/s3viewer.py'],
             binaries=[],
             datas=[('src/assets/*')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='s3viewer',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='packaging/icons/icon.ico')

# Package the executable file into .app if on OS X
if sys.platform == 'darwin':
    app = BUNDLE(exe,
                name='s3viewer.app',
                info_plist= { 'NSHighResolutionCapable': 'True'},
                icon='packaging/icons/icon.icns')