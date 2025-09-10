# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file per Gestionale Scuola di Danza

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Percorsi di base
block_cipher = None
project_dir = os.path.dirname(os.path.abspath(__file__))

# Collect data files per WeasyPrint e altre dipendenze
weasyprint_data = collect_data_files('weasyprint')
cffi_data = collect_data_files('cffi')
cairocffi_data = collect_data_files('cairocffi')
cairosvg_data = collect_data_files('cairosvg') 
html5lib_data = collect_data_files('html5lib')
cssselect2_data = collect_data_files('cssselect2')
tinycss2_data = collect_data_files('tinycss2')

# Collect submodules per Flask e SQLAlchemy
flask_submodules = collect_submodules('flask')
sqlalchemy_submodules = collect_submodules('sqlalchemy')
jinja2_submodules = collect_submodules('jinja2')

# Dati da includere nell'eseguibile
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('models', 'models'),
    ('utils', 'utils'),
]

# Aggiungi i dati delle dipendenze
datas.extend(weasyprint_data)
datas.extend(cffi_data)
datas.extend(cairocffi_data)
datas.extend(cairosvg_data)
datas.extend(html5lib_data)
datas.extend(cssselect2_data)
datas.extend(tinycss2_data)

# Moduli nascosti necessari
hiddenimports = [
    'flask',
    'flask_sqlalchemy', 
    'sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'sqlalchemy.sql',
    'sqlalchemy.sql.default_comparator',
    'werkzeug',
    'werkzeug.security',
    'jinja2',
    'jinja2.ext',
    'bcrypt',
    'weasyprint',
    'weasyprint.css',
    'weasyprint.css.targets',
    'weasyprint.css.style_for',
    'weasyprint.html',
    'weasyprint.html.get_html_metadata',
    'cairocffi',
    'cffi',
    'cairosvg',
    'html5lib',
    'cssselect2',
    'tinycss2',
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.colors',
    'reportlab.lib.units',
    'reportlab.lib.enums',
    'PIL',
    'PIL.Image',
    'models',
    'models.cliente',
    'models.corso', 
    'models.insegnante',
    'models.pagamento',
    'utils',
    'utils.stampa_pdf',
]

# Aggiungi i moduli automaticamente rilevati
hiddenimports.extend(flask_submodules)
hiddenimports.extend(sqlalchemy_submodules)
hiddenimports.extend(jinja2_submodules)

# Binari da escludere per ridurre dimensioni
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'IPython',
    'notebook',
    'jupyter',
]

a = Analysis(
    ['app.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Rimuovi duplicati
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Configurazione eseguibile
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='gestionale_danza',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compressione UPX per ridurre dimensioni
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Non mostrare console Windows
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Aggiungi un'icona se disponibile: icon='icon.ico'
)

# Informazioni di versione per Windows
if sys.platform.startswith('win'):
    exe.version_info = {
        'FileVersion': (1, 0, 0, 0),
        'ProductVersion': (1, 0, 0, 0),
        'FileDescription': 'Gestionale Scuola di Danza',
        'InternalName': 'gestionale_danza',
        'OriginalFilename': 'gestionale_danza.exe',
        'ProductName': 'Gestionale Scuola di Danza',
        'CompanyName': 'Scuola di Danza',
        'LegalCopyright': '© 2024 Scuola di Danza',
    }