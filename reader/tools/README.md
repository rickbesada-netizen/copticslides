# Extraction tools

Python scripts used to turn the two source PDFs into the app's JSON data.
They were run on Linux with: pdfplumber/pdfminer.six, PyMuPDF, fontTools, OpenCV, Pillow,
tesserocr (Tesseract 5 with `eng` best and `ara` best models), scikit-learn and wordfreq.

Resurrection Feast (text PDF exported from PowerPoint)
1. `cidchars.py`   – extract every character with its glyph id, font and position
2. `res_extract.py` – convert legacy Coptic fonts (`coptic_fonts.py`) and decode Arabic glyphs
3. `res_build.py`  – group slides into sections and rows; separates the book's printed phonetics
4. `fix_coptic_split.py` – rejoins Coptic words split by slide justification

Holy Pascha (scanned PDF)
1. render pages at 300 dpi (pdftoppm), `pascha_seg.py` – row/column layout (XY-cut)
2. `pascha_run.py` – script detection and OCR per cell (English, Arabic; Coptic kept as image)
3. `pascha_fix.py` – second passes (Arabic re-read, re-test cells first marked Coptic)
4. `headers.py`    – running page headers, used to place the hour boundaries
5. `copglyph.py` + `copocr.py` – Coptic glyph classifier trained on this book's typeface
6. `pascha_toc.py` + `pascha_build.py` – table of contents and final JSON per day
7. `build_library.py` – writes data/library.json

Paths inside the scripts point at the original working folders; adjust them before re-running.
