"""Build reader/data/katameros.json from the two Katameros PDFs.

  * katameros-days.pdf    (Days of the Year: every Coptic date, with its "instead read" table)
  * katameros-sundays.pdf (normal Sundays by month, the fifth Sunday, Sundays of Great Lent
                           and of the Holy Fifty Days, and the Lord's feasts)

Only the reading REFERENCES are stored (book, chapter:verses) for Vespers, Matins and the
Liturgy, plus the book page so the reading can be found. The reading text is not copied.

usage: python build_katameros.py katameros-days.pdf katameros-sundays.pdf out.json
"""
import json, re, subprocess, sys

MONTHS = {'TUT': 1, 'BABAH': 2, 'HATUR': 3, 'KIYAHK': 4, 'KYIAHK': 4, 'KIAHK': 4, 'TUBAH': 5, 'AMSHIR': 6,
          'BARAMHAT': 7, 'BARAMUDAH': 8, 'BARAMODA': 8, 'BASHANS': 9, 'BASHANCE': 9, 'BAUNAH': 10, 'ABIB': 11,
          'MISRA': 12, 'AL-NASI': 13, 'NASI': 13}
BOOKS = {
    'PSALM': 'Psalm', 'PSALMS': 'Psalm', 'MATTHEW': 'Matthew', 'MARK': 'Mark', 'LUKE': 'Luke', 'JOHN': 'John',
    'ACTS': 'Acts', 'ROMANS': 'Romans', '1 CORINTHIANS': '1 Corinthians', '2 CORINTHIANS': '2 Corinthians',
    'GALATIANS': 'Galatians', 'EPHESIANS': 'Ephesians', 'PEHESIANS': 'Ephesians', 'PHILIPPIANS': 'Philippians',
    'COLOSSIANS': 'Colossians', '1 THESSALONIANS': '1 Thessalonians', '2 THESSALONIANS': '2 Thessalonians',
    '1 TIMOTHY': '1 Timothy', '2 TIMOTHY': '2 Timothy', 'TITUS': 'Titus', 'PHILEMON': 'Philemon',
    'HEBREWS': 'Hebrews', 'JAMES': 'James', '1 PETER': '1 Peter', '2 PETER': '2 Peter', '1 JOHN': '1 John',
    '2 JOHN': '2 John', '3 JOHN': '3 John', 'JUDE': 'Jude', 'REVELATION': 'Revelation'}
ORD = {'FIRST': 1, 'SECOND': 2, 'THIRD': 3, 'FOURTH': 4, 'FIFTH': 5, 'SIXTH': 6}
REFLINE = re.compile(r'^\s*((?:[1-3] ?)?[A-Za-z]+)\s*(\d+\s*:\s*[\d\s:,\-&;]+)\s*$')


def month_no(s):
    return MONTHS.get(s.upper().replace(' ', ''))


def pdf_pages(pdf):
    return subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout.split('\f')


def read_sections(pages, offset, starts):
    """Reading references of each section (from its start page to the next section's start).
    Returns {start_page: {'vespers': [...], 'matins': [...], 'liturgy': [...]}}"""
    out, carry = {}, []
    for k, start in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else min(start + 12, len(pages) - offset)
        svc, sec = 'vespers', {'vespers': carry, 'matins': [], 'liturgy': [], 'next': []}
        carry = []
        for pg in range(start, end):
            for line in pages[pg + offset].split('\n'):
                s = line.strip()
                if len(s) < 60 and re.search(r'\bVespers\b', s, re.I):
                    # a Vespers heading after the Liturgy belongs to the next section
                    svc = 'next' if sec['liturgy'] else 'vespers'; continue
                if len(s) < 60 and re.search(r'\bMatins?', s, re.I) and svc != 'next' and not re.search(r'procession', s, re.I):
                    svc = 'matins'; continue
                if re.match(r'^LITURGY\b', s) and svc != 'next':
                    svc = 'liturgy'; continue
                m = REFLINE.match(line)
                if not m: continue
                bk = re.sub(r'^([1-3]) ?', r'\1 ', m.group(1).upper())
                if bk in BOOKS:
                    ref = re.sub(r'\s+', ' ', m.group(2)).replace(' :', ':').replace(': ', ':').strip(' ,;&')
                    sec[svc].append({'book': BOOKS[bk], 'ref': ref})
        carry = sec.pop('next')
        out[start] = sec
    return out


def shape(sec):
    p = lambda l, i: l[i] if i < len(l) else None
    v, m, l = sec.get('vespers', []), sec.get('matins', []), sec.get('liturgy', [])
    if len(v) == 4: v = v[2:]  # a Lent Sunday's evening prayer carried over from the previous Sunday
    return {'vespers': {'psalm': p(v, 0), 'gospel': p(v, 1)},
            'matins': {'psalm': p(m, 0), 'gospel': p(m, 1)},
            'liturgy': {'pauline': p(l, 0), 'catholic': p(l, 1), 'acts': p(l, 2), 'psalm': p(l, 3), 'gospel': p(l, 4)},
            'count': [len(v), len(m), len(l)]}


def build_days(pdf):
    pages, OFFSET = pdf_pages(pdf), 32  # printed page = pdf page index - 32
    days, cur = {}, None
    row = re.compile(r'^(\d{1,2}) (Tut|Babah|Hatur|Kiyahk|Kyiahk|Tubah|Amshir|Baramhat|Baramudah|Baramoda|Bashans|Bashance|Baunah|Abib|Misra|Al-Nasi)\s+(.*?)\s*$')
    for pi in range(20, OFFSET + 40):
        for line in pages[pi].split('\n'):
            m = row.match(line)
            if m:
                d, mon, rest = int(m.group(1)), month_no(m.group(2)), m.group(3)
                pm = re.search(r'\s{2,}(?:(\d{1,2}) ([A-Za-z-]+)\s+)?(\d{1,3})$', rest) or re.search(r'^(?:(\d{1,2}) ([A-Za-z-]+)\s+)?(\d{1,3})$', rest)
                cur = {'occ': rest[:pm.start()].strip() if pm else rest, 'page': int(pm.group(3)) if pm else None,
                       'instead': [int(pm.group(1)), month_no(pm.group(2))] if pm and pm.group(1) else None}
                days[f'{mon}-{d}'] = cur
            elif cur and line.startswith(' ' * 8) and line.strip() and not re.search(r'Readings Throughout|DAY\s+OCCASION|BLESSED MONTH', line):
                part = re.split(r'\s{2,}', line.strip())[0]
                if not re.fullmatch(r'\d+', part): cur['occ'] = (cur['occ'] + ' ' + part).strip()
            elif 'BLESSED MONTH' in line:
                cur = None
    # contents list ("12 Hatur    159") = true section starts; snap table pages onto them
    starts = sorted({int(m.group(1)) for pi in range(0, OFFSET + 40) for m in
                     re.finditer(r'(?m)^\s+\d{1,2} [A-Za-z-]+\s+(\d{2,3})\s*$', pages[pi])})
    for v in days.values():
        if v['page'] and v['page'] not in starts:
            v['page'] = max([s for s in starts if s <= v['page']] or [v['page']])
    secs = read_sections(pages, OFFSET, starts)
    return {key: {'occasion': re.sub(r'\s+', ' ', v['occ']), 'page': v['page'], 'instead': v['instead'],
                  **shape(secs.get(v['page'], {}))} for key, v in days.items()}


def build_sundays(pdf):
    pages, OFFSET = pdf_pages(pdf), -1  # printed page = pdf page index + 1
    toc = []
    for pi in range(0, 30):
        for m in re.finditer(r'(?m)^\s*[<E]\s+(.+?)\s*\.{2,}\s*(\d{2,3})\s*$', pages[pi]):
            toc.append((m.group(1).strip(), int(m.group(2))))
    starts = sorted({p for _, p in toc})
    secs = read_sections(pages, OFFSET, starts)
    res = {}
    for name, page in toc:
        m = re.match(r'(First|Second|Third|Fourth) Sunday of ([A-Za-z-]+)$', name)
        if m and month_no(m.group(2)): key = f'{month_no(m.group(2))}-{ORD[m.group(1).upper()]}'
        elif 'short month' in name: key = '13-1'
        elif name.startswith('The fifth Sunday'): key = 'fifth'
        elif name.startswith('Pre-Lent'): key = 'lent-0'
        elif (m := re.match(r'(First|Second|Third|Fourth|Fifth|Sixth) Sunday of Lent', name)): key = f'lent-{ORD[m.group(1).upper()]}'
        elif name.startswith('Palm Sunday'): key = 'palm'
        elif name.startswith('Easter'): key = 'easter'
        elif (m := re.match(r'(First|Second|Third|Fourth|Fifth|Sixth) Sunday of Pentecost', name)): key = f'pent-{ORD[m.group(1).upper()]}'
        elif name.startswith('Ascension'): key = 'ascension'
        elif name.startswith('The Great Pentecost'): key = 'pentecost'
        else: key = 'feast:' + name
        res[key] = {'occasion': name, 'page': page, **shape(secs.get(page, {}))}
    return res


def main(days_pdf, sundays_pdf, out):
    days, sundays = build_days(days_pdf), build_sundays(sundays_pdf)
    json.dump({'source': 'Katameros: Days of the Year; Katameros of the Sundays (St Mary Coptic Orthodox Church, Ottawa). References only.',
               'days': days, 'sundays': sundays}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(len(days), 'days; unusual:', [k for k, v in days.items() if v['count'] != [2, 2, 5]])
    print(len(sundays), 'sundays; unusual:', [(k, v['count']) for k, v in sundays.items() if v['count'] != [2, 2, 5]])


if __name__ == '__main__':
    main(*sys.argv[1:4])
