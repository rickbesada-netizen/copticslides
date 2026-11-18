# Liturgy Reader

An offline-capable Coptic liturgical reader, organised like a content library
(Agpeya, Psalmody, Bible, Liturgies, Readings, Melodies, Index, Clergy, Special), built from four books:

* **Agpia** (C.O.P.T. Sydney, NKJV psalms): every hour, the Veil, Midnight, absolutions.
* **The Service of the Deacon** (St Demiana & St Athanasius, Sydney): Offering of Incense, doxologies,
  the Liturgies of St Basil, St Gregory and St Cyril, fractions, communion and seasonal hymns, seasonal
  responses, Tamgeed, Betrothal and Matrimony, in English, Arabic in English letters, Coptic in English
  letters and Coptic.

* **Book of the Holy Pascha**: Last Friday of Lent, Holy Unction, Lazarus Saturday, Palm Sunday,
  every hour of Holy Week (eve and day), Covenant Thursday, Good Friday, the Book of Psalms,
  Bright Saturday, the Book of Revelation and the Resurrection Feast Eve.
* **Feast of the Resurrection (2015)**: evening incense, Verses of the Cymbals, Seven Tunes,
  doxologies, matins and the full Feast Liturgy. This is the layout template
  (English | Coptic | Arabic, black background, gold text).

## Features

* Columns you choose and order: **English, Coptic, Arabic, Coptic in English letters,
  Coptic in Arabic letters, Arabic in English letters, English in Arabic letters**.
* Uses the book's own printed phonetics when present; otherwise phonetics are generated
  (`js/translit.js`, Greco-Bohairic church pronunciation).
* English Scripture: NKJV, as printed in the books (see notes below).
* Coptic calendar: today's Coptic date, Orthodox Easter, and a "Today's service" button during
  Holy Week that opens the right day and hour (plus "Tonight" for the eve hours).
* Presentation mode: full-screen, one row at a time, auto-fit text, keyboard/swipe/click navigation,
  for projecting in church.
* Search across English, Coptic and Arabic (Arabic search ignores vowel marks and hamza forms).
* App language: English, العربية, Français, Español, Deutsch, Italiano.
* Themes: Projector (book style), Dark, Light, Sepia. Adjustable text size, side-by-side or stacked layout.
* Installable app (PWA) that works offline after first use.

## Run locally

Any static web server works, e.g.

```
cd CopticReader
python -m http.server 8080
```

then open http://localhost:8080. (Opening `index.html` directly from disk will not load the data
because browsers block `fetch` on `file://`.)

## Install on a phone

Open the hosted site in Chrome (Android) or Safari (iPhone) → menu → **Add to Home screen**.
It then opens full-screen like a native app and works offline.

## Project layout

```
index.html, css/, js/          the app (no build step, plain JavaScript)
js/translit.js                 transliteration engines (Coptic↔Latin/Arabic, Arabic→Latin, English→Arabic)
js/calendar.js                 Coptic calendar and Easter computus
js/i18n.js                     interface translations
data/library.json              books → groups → sections
data/resurrection.json         Resurrection Feast content
data/pascha/*.json             Holy Pascha content (one file per day)
img/res/                       Resurrection slides that are pictures only (hymn vocalisation charts etc.)
img/cop/                       Coptic text from the Pascha scan, cropped exactly as printed
tools/                         the scripts used to extract the books (Python)
```

### Content format

Each section is `{ id, title: {en, ar}, rows: [...] }`. A row can have:

| key       | meaning                                                     |
|-----------|-------------------------------------------------------------|
| `en`      | English                                                     |
| `cop`     | Coptic (Unicode)                                            |
| `cop_img` | Coptic as printed (image paths), used for the Pascha book    |
| `ar`      | Arabic                                                      |
| `en_ph`   | phonetics printed in the book (English letters)             |
| `ar_ph`   | phonetics printed in the book (Arabic letters)              |
| `img`     | a picture-only slide                                        |
| `kind`    | `heading` or `rubric`                                       |

To add more services (e.g. Kiahk, Annual Psalmody), add a JSON file in `data/` with the same
shape and list its sections in `data/library.json`.

## Notes on the sources

* **Resurrection book**: text was extracted directly from the PDF. Its Coptic was typed in the old
  Athanasius / CS fonts and has been converted to Unicode Coptic; its Arabic was decoded from the
  font glyphs. Arabic vowel marks were removed because their positions in the PDF were unreliable.
* **Pascha book**: the PDF is a scan, so English and Arabic were read with OCR. Coptic is shown as
  the printed scan by default (exact). A machine-read Coptic text is also included for search and
  phonetics; it can be shown instead in Settings and may contain small errors.
* **NKJV**: New Testament readings are NKJV in both books. The Pascha book's Old Testament
  prophecies and Psalms are translated from the Septuagint (as the Coptic Church reads them), so
  they follow the book rather than the NKJV wording.
