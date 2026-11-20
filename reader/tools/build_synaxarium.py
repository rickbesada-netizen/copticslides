"""Build reader/data/synaxarium.json from synaxarium.pdf: one entry per Coptic date
({month}-{day}: title lines + text), keyed by the book's own day headings
("The Twelfth Day of the Blessed Month of Hatour"). The first copy of a day wins
(the PDF repeats 21-30 Babah).

usage: python build_synaxarium.py synaxarium.pdf out.json
"""
import json, re, subprocess, sys

MONTHS = {'tute': 1, 'babah': 2, 'hatour': 3, 'kiahk': 4, 'tubah': 5, 'amshir': 6, 'baramhat': 7, 'baramoudah': 8,
          'barnmoudah': 8, 'baramouda': 8, 'bashans': 9, 'baounah': 10, 'abib': 11, 'misra': 12, 'mesra': 12, 'el-nasi': 13, 'nasi': 13}
UNITS = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'forth': 4, 'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9,
         'tenth': 10, 'eleventh': 11, 'twelfth': 12, 'thirteenth': 13, 'fourteenth': 14, 'fifteenth': 15, 'sixteenth': 16,
         'seventeenth': 17, 'eighteenth': 18, 'nineteenth': 19, 'twentieth': 20, 'thirtieth': 30}


def ordinal(s):
    s = s.lower().replace('-', ' ').split()
    if len(s) == 2 and s[0] == 'twenty': return 20 + UNITS.get(s[1], 0)
    return UNITS.get(s[0]) if len(s) == 1 else None


def main(pdf, out):
    text = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    lines = text.replace('\f', '\n').split('\n')
    head = re.compile(r'^\s*The ([A-Za-z-]+(?: [A-Za-z-]+)?) Day\d*(?: of the Bless\w* Mo[nu]th of ([A-Za-z-]+))?[\s.()\d]*$', re.I)
    mhead = re.compile(r'^\s*The Bless\w* Month of ([A-Za-z-]+)[\s.]*(?:\(.*\))?\s*$', re.I)
    marks, month = [], None
    for i, l in enumerate(lines):
        m = mhead.match(l)
        if m and m.group(1).lower() in MONTHS: month = MONTHS[m.group(1).lower()]; continue
        m = head.match(l)
        if m:
            d = ordinal(m.group(1))
            mo = MONTHS.get((m.group(2) or '').lower(), month if not m.group(2) else None)
            if d and mo: marks.append((i, mo, d)); month = mo
    entries = {}
    for k, (i, mo, d) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        body = [l.strip() for l in lines[i + 1:end]]
        body = [l for l in body if not re.fullmatch(r'\d{1,3}|One God\. Amen|In the name of the Father.*', l)]
        if body and mhead.match(body[-1] or ''): body = body[:-1]
        txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(body)).strip()
        # paragraphs: join wrapped lines
        paras = [re.sub(r'\s*\n\s*', ' ', p).strip() for p in re.split(r'\n\s*\n', txt) if p.strip()]
        key = f'{mo}-{d}'
        if key in entries: continue
        titles, rest = [], paras
        if paras and re.match(r'^[1I]\.\s', paras[0]):
            titles = [t.strip() for t in re.split(r'\s(?=\d\.\s)', re.sub(r'^I\.', '1.', paras[0]))]
            rest = paras[1:]
        elif paras:
            titles, rest = [paras[0]], paras[1:]
        entries[key] = {'titles': titles, 'paras': rest}
    json.dump({'source': 'Coptic Synaxarium (English)', 'days': entries}, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    L = [30] * 12 + [6]
    missing = [f'{m}-{d}' for m in range(1, 14) for d in range(1, L[m - 1] + 1) if f'{m}-{d}' not in entries]
    print(len(entries), 'days; missing:', missing)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
