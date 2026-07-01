# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec per pdf_converter.

Build: pyinstaller build.spec
Produce un singolo .exe in dist/pdf_converter.exe

PRIMA DELLA BUILD:
  - updater.py (root): imposta VERSION_JSON_URL con l'URL reale del version.json
  - src/backend/alternative/extract_ocr.py: imposta _BUILD_API_KEY con la Mistral API key
  (Le costanti _BUILD_* vengono embeddate nel .exe; nel repo sono vuote per non
   esporre credenziali. In dev si usano variabili d'ambiente o CLI flags.)
"""

from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'src.backend.server',
        'src.backend.main',
        'src.backend.pdf_to_exel_converter',
        'src.backend.pdf_fallback',
        'src.backend.io.file_manager',
        'src.backend.extraction.pdf_reader',
        'src.backend.extraction.layouts',
        'src.backend.processing.table_processor',
        'src.backend.export.excel_writer',
        'src.backend.utils.table_utils',
        'src.backend.alternative.main',
        'src.backend.alternative.extract_ocr',
        'src.backend.alternative.html_to_excel',
        'src.backend.alternative.processing',
        'pdfplumber',
        'pandas',
        'openpyxl',
        'fitz',
        'PyPDF2',
        'reportlab',
        'mistralai',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.middleware',
        'updater',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'PIL.ImageShow', 'PIL.ImageQt'],
    noarchive=False,
)

# Include frontend build statico (se esiste)
frontend_dist = Path('src/frontend/dist')
if frontend_dist.is_dir():
    for f in frontend_dist.rglob('*'):
        if f.is_file():
            rel_path = str(f.relative_to(frontend_dist.parent))
            a.datas.append((rel_path, str(f), 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pdf_converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
