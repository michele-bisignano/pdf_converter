```text
pdf_converter/
├── .claude/
│   ├── settings.local.json
│   └── wiki/
│       ├── hot.md
│       ├── memory/
│       │   ├── architecture.md
│       │   ├── decisions.md
│       │   ├── gotchas.md
│       │   └── INDEX.md
│       └── raw/
│           └── README.md
├── .gitignore
├── .ruff_cache/
├── build.spec
├── CLAUDE.md
├── docs/
│   ├── project_structure/
│   │   └── repository_tree.md
│   └── UPDATER_SETUP.md
├── file_example/
├── LICENSE
├── Logo/
│   └── PDFtoEXCEL_Converter.png
├── main.py
├── output/
├── README.md
├── requirements.txt
├── scripts/
│   └── auto-update.sh
├── src/
│   ├── __init__.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── alternative/
│   │   │   ├── __init__.py
│   │   │   ├── extract_ocr.py
│   │   │   ├── html_to_excel.py
│   │   │   ├── main.py
│   │   │   └── processing.py
│   │   ├── export/
│   │   │   ├── __init__.py
│   │   │   └── excel_writer.py
│   │   ├── extraction/
│   │   │   ├── __init__.py
│   │   │   ├── layouts.py
│   │   │   └── pdf_reader.py
│   │   ├── io/
│   │   │   ├── __init__.py
│   │   │   └── file_manager.py
│   │   ├── main.py
│   │   ├── pdf_fallback.py
│   │   ├── pdf_to_exel_converter.py
│   │   ├── processing/
│   │   │   ├── __init__.py
│   │   │   └── table_processor.py
│   │   ├── server.py
│   │   ├── update_router.py
│   │   ├── updater.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── table_utils.py
│   └── frontend/
│       ├── .gitignore
│       ├── .oxlintrc.json
│       ├── index.html
│       ├── package-lock.json
│       ├── package.json
│       ├── postcss.config.js
│       ├── public/
│       │   ├── favicon.svg
│       │   └── icons.svg
│       ├── README.md
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   │   ├── PDFConverterBox.jsx
│       │   │   └── UpdateBanner.jsx
│       │   ├── index.css
│       │   ├── main.jsx
│       │   └── services/
│       │       └── api.js
│       └── vite.config.js
├── temp/
└── tools/
    └── project_tree/
        ├── generate_tree.py
        ├── README.md
        └── setup_hook.py
```
