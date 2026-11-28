"""Extract the three-column rite books (Coptic | English | Arabic, Word tables) into reader data.

Works for the St Bishoy "Rites" PDFs: Baptism, Laqan of the Apostles, Prostration (Sagda),
Laqan of Epiphany. Table rows are found from the vertical rules (x ~ 258 and ~ 401);
text outside the tables is a heading (large / coloured / centred) or a rubric (red).
Coptic is typed in CS Avva Shenouda and converted to Unicode; Arabic is put back into
reading order (the PDF stores it visually, left to right).

usage: python build_rites.py book.pdf out.json prefix "Part title|first page|ar title" ...
"""
import json, re, sys, unicodedata
import pdfplumber
sys.path.insert(0, __import__('os').path.dirname(__file__))
from coptic_fonts import convert

C1, C2 = 258.5, 401.5          # column rules: Coptic | English | Arabic
AR_RE = re.compile(r'[؀-ۿ]')
HARAKAT = re.compile(r'[ً-ْٰـ]')
ROLE = {'priest': 'PRIEST', 'deacon': 'DEACON', 'people': 'PEOPLE', 'congregation': 'PEOPLE', 'reader': 'READER',
        'bishop': 'BISHOP', 'all': 'ALL', 'priests': 'PRIEST', 'deacons': 'DEACON', 'chanters': 'PEOPLE',
        'cantor': 'PEOPLE', 'the priest': 'PRIEST', 'the deacon': 'DEACON', 'the people': 'PEOPLE', 'high priest': 'PRIEST',
        'the high priest': 'PRIEST', 'pope': 'BISHOP', 'presbyter': 'PRIEST', 'godparent': 'ALL', 'godparents': 'ALL',
        'the catechumen': 'ALL', 'catechumen': 'ALL'}


def is_red(c):
    col = c.get('non_stroking_color') or (0,)
    return len(col) == 3 and col[0] > 0.5 and col[1] < 0.3


def is_colour(c):
    col = c.get('non_stroking_color') or (0,)
    return len(col) == 3 and max(col) > 0.3


def coptic_font(c):
    return 'Avva' in c['fontname'] or 'Shenou' in c['fontname']


def lines_of(chars, tol=3):
    """group chars into lines (by top), each line sorted left to right"""
    out = []
    for c in sorted(chars, key=lambda c: (round(c['top']), c['x0'])):
        if out and abs(out[-1][0]['top'] - c['top']) <= tol:
            out[-1].append(c)
        else:
            out.append([c])
    return [sorted(l, key=lambda c: c['x0']) for l in out]


def text_ltr(line):
    s, prev = '', None
    for c in line:
        if prev is not None and c['x0'] - prev['x1'] > c['size'] * 0.15 and not s.endswith(' ') and c['text'] != ' ':
            s += ' '
        s += c['text']; prev = c
    return s


def text_coptic(line):
    # convert each run in a Coptic font; leave other runs as they are
    out, run, font = [], [], None
    def flush():
        if run:
            t = ''.join(x['text'] for x in run)
            out.append(convert(t, 'CS Avva Shenouda') if font else t)
    prev = None
    for c in line:
        cf = coptic_font(c)
        gap = prev is not None and c['x0'] - prev['x1'] > c['size'] * 0.25 and c['text'] != ' '
        if cf != font or gap:
            flush(); run = []
            if gap and out and not out[-1].endswith(' '): out.append(' ')
            font = cf
        run.append(c); prev = c
    flush()
    return ''.join(out)


def text_rtl(line):
    chars = sorted(line, key=lambda c: -(c['x0'] + c['x1']) / 2)
    s, left = '', None
    for c in chars:
        if HARAKAT.match(c['text']):
            left = min(left, c['x0']) if left is not None else c['x0']; continue
        if left is not None and left - c['x1'] > c['size'] * 0.16 and not s.endswith(' ') and c['text'] != ' ':
            s += ' '
        s += c['text']; left = c['x0'] if left is None else min(left, c['x0'])
    # runs of digits / Latin were written left to right: put them back
    s = re.sub(r'[0-9A-Za-z][0-9A-Za-z.:\-/]*[0-9A-Za-z]|[0-9A-Za-z]', lambda m: m.group(0)[::-1], s)
    s = re.sub(r'(\S) ا(?=[\s.،:؛!؟]|$)', r'\1ا', s)   # alef of a dropped tanween
    return unicodedata.normalize('NFKC', s)


def join_lines(parts):
    s = ''
    for p in parts:
        p = p.strip()
        if not p: continue
        if s.endswith('-') and not s.endswith(' -'): s = s[:-1] + p
        else: s = (s + ' ' + p) if s else p
    return re.sub(r'\s+', ' ', s).strip()


def cell_paras(chars, kind):
    """paragraphs of one column of one table row: [(text, red, first_line_red)]"""
    ls = lines_of(chars)
    paras, cur, last_bottom = [], [], None
    for l in ls:
        if not ''.join(c['text'] for c in l).strip(): continue
        top = min(c['top'] for c in l)
        size = max(c['size'] for c in l)
        if cur and top - last_bottom > size * (1.25 if kind != 'cop' else 1.05):
            paras.append(cur); cur = []
        cur.append(l); last_bottom = max(c['bottom'] for c in l)
    if cur: paras.append(cur)
    fn = {'cop': text_coptic, 'en': text_ltr, 'ar': text_rtl}[kind]
    out = []
    for p in paras:
        reds = [is_red(c) for l in p for c in l if c['text'].strip()]
        out.append({'lines': [fn(l) for l in p], 'red': sum(reds) > len(reds) / 2 if reds else False,
                    'top': min(c['top'] for c in p[0])})
    return out


def band_paras(cols):
    """split one table row into paragraphs. Paragraphs start with an indented line (or a role
    label) in the English column; Coptic and Arabic lines are assigned to the paragraph whose
    start is just above them."""
    L = {k: [l for l in lines_of(v) if ''.join(c['text'] for c in l).strip()] for k, v in cols.items()}
    def starts(lines, left, indent):
        out = []
        for i, l in enumerate(lines):
            x0 = min(c['x0'] for c in l if c['text'].strip())
            txt = ''.join(c['text'] for c in l).strip()
            prev = ''.join(c['text'] for c in lines[i - 1]).strip() if i else ''
            if i == 0 or x0 > left + indent or role_of(txt)[0] and len(txt) < 25 or (role_of(prev)[0] and len(prev) < 25):
                out.append(min(c['top'] for c in l))
        return out
    anchors = starts(L['en'], (C1 if C1 > 0 else 70) + 2, 12) if L['en'] else starts(L['cop'], 70, 10) if L['cop'] else [min(c['top'] for c in L['ar'][0])] if L['ar'] else []
    if not anchors: return []
    fn = {'cop': text_coptic, 'en': text_ltr, 'ar': text_rtl}
    paras = [{k: {'lines': [], 'red': []} for k in cols} for _ in anchors]
    for k, lines in L.items():
        for l in lines:
            top = min(c['top'] for c in l)
            j = max([i for i, a in enumerate(anchors) if a <= top + 7] or [0])
            paras[j][k]['lines'].append(fn[k](l))
            paras[j][k]['red'] += [is_red(c) for c in l if c['text'].strip()]
    out = []
    for p in paras:
        g = {}
        for k, v in p.items():
            g[k] = {'lines': v['lines'], 'red': sum(v['red']) > len(v['red']) / 2} if v['lines'] else None
        out.append(g)
    return out


def role_of(en):
    m = re.match(r'^\s*([A-Za-z][A-Za-z ]{1,24}?)\s*:\s*(.*)$', en or '')
    if m and m.group(1).strip().lower() in ROLE:
        return ROLE[m.group(1).strip().lower()], m.group(2).strip()
    return None, en


def page_rows(page):
    """rows of one page, in reading order"""
    global C1, C2
    # column rules: 3 columns (Coptic | English | Arabic) at ~258/401, or 2 columns (English | Arabic) at ~337
    vx = {}
    for e in page.edges:
        if e['orientation'] == 'v': vx[round(e['x0'])] = vx.get(round(e['x0']), 0) + e['bottom'] - e['top']
    has = lambda x: sum(v for k, v in vx.items() if abs(k - x) <= 3) > 20
    if has(258) or has(401): C1, C2, RULE = 258.5, 401.5, 258.5
    elif has(337): C1, C2, RULE = -1, 337.5, 337.5
    else: C1, C2, RULE = 258.5, 401.5, 258.5
    edges = sorted({(round(e['top'], 1), round(e['bottom'], 1)) for e in page.edges
                    if e['orientation'] == 'v' and RULE - 4 < e['x0'] < RULE + 4 and e['bottom'] - e['top'] > 1})
    # merge touching segments into table rows (each Word row is one or more segments)
    bands = []
    for t, b in edges:
        if bands and t - bands[-1][1] < 0.6 and (b - t) < 6: bands[-1][1] = max(bands[-1][1], b); continue
        bands.append([t, b])
    bands = [b for b in bands if b[1] - b[0] > 6]
    chars = [c for c in page.chars if c['top'] < 722]            # drop page number
    inband = lambda c: next((i for i, (t, b) in enumerate(bands) if t - 2 <= (c['top'] + c['bottom']) / 2 <= b + 2), None)
    groups, free = {}, []
    for c in chars:
        i = inband(c)
        if i is None: free.append(c)
        else: groups.setdefault(i, []).append(c)
    items = []
    # free text: headings and rubrics
    for l in lines_of(free):
        if not ''.join(c['text'] for c in l).strip(): continue
        items.append(('free', min(c['top'] for c in l), l))
    for i, cs in groups.items():
        items.append(('band', bands[i][0], cs))
    items.sort(key=lambda x: x[1])
    rows = []
    pending = None   # heading lines collected until the next non-heading
    for kind, top, data in items:
        if kind == 'free':
            l = data
            ar = [c for c in l if AR_RE.match(c['text'])]
            if ar:   # digits and brackets inside the Arabic text belong to it
                ax0, ax1 = min(c['x0'] for c in ar), max(c['x1'] for c in ar)
                ar = [c for c in l if AR_RE.match(c['text']) or (ax0 - 2 <= c['x0'] and c['x1'] <= ax1 + 2)]
            lat = [c for c in l if c not in ar and c['text'].strip()]
            size = max(c['size'] for c in l if c['text'].strip())
            x0, x1 = min(c['x0'] for c in l if c['text'].strip()), max(c['x1'] for c in l if c['text'].strip())
            centred = abs((x0 + x1) / 2 - 306) < 40 and x1 - x0 < 470
            coloured = any(is_colour(c) for c in l if c['text'].strip())
            txtlen = len(''.join(c['text'] for c in l).strip())
            heading = coloured and (size >= 14 or (centred and txtlen < 70) or not any(is_red(c) for c in l if c['text'].strip()))
            # a rubric split in two columns (English left, Arabic right) on the same line
            en = text_coptic(lat) if lat and all(coptic_font(c) or not c['text'].strip() for c in lat) else text_ltr(lat) if lat else ''
            art = text_rtl(ar) if ar else ''
            k = 'heading' if heading else ('rubric' if coloured else 'text')
            prev = rows[-1] if rows and rows[-1].get('_free') else None
            near = prev is not None and abs(top - prev['_bottom']) < size * 1.6
            same = prev is not None and prev['kind'] == k and not (k == 'heading' and en and prev.get('ar'))
            # the Arabic half of a red rubric often sits beside it and is centred: keep it with the rubric
            arabic_half = prev is not None and prev['kind'] == 'rubric' and not en and art
            if near and (same or arabic_half):
                r = rows[-1]
                if en: r['en'] = join_lines([r.get('en', ''), en])
                if art: r['ar'] = join_lines([r.get('ar', ''), art])
                r['_bottom'] = max(c['bottom'] for c in l)
            else:
                r = {'kind': k, '_free': True, '_bottom': max(c['bottom'] for c in l)}
                if en.strip(): r['en'] = en.strip()
                if art.strip(): r['ar'] = art.strip()
                rows.append(r)
            continue
        cs = data
        mid = lambda c: (c['x0'] + c['x1']) / 2
        cols = {'cop': [c for c in cs if mid(c) < C1], 'en': [c for c in cs if C1 <= mid(c) < C2], 'ar': [c for c in cs if mid(c) >= C2]}
        P = band_paras(cols)
        n = len(P)
        for j in range(n):
            g = P[j]
            en = join_lines(g['en']['lines']) if g['en'] else ''
            cop = join_lines(g['cop']['lines']) if g['cop'] else ''
            ar = join_lines(g['ar']['lines']) if g['ar'] else ''
            role, rest = role_of(en)
            if role:
                rows.append({'kind': 'role', 'role': role})
                # the role label sits on its own line above the text in each column
                en = rest
                cop = re.sub(r'^\S+\s*[:@]\s*', '', cop, count=1) if cop else cop
                ar = re.sub(r'^[^:]{1,25}:\s*', '', ar, count=1) if ar else ar
            red = g['en']['red'] if g['en'] else (g['cop']['red'] if g['cop'] else False)
            r = {}
            if en: r['en'] = en
            if cop: r['cop'] = cop
            if ar: r['ar'] = ar
            if not r or re.fullmatch(r'\d{1,3}', r.get('en', '') + r.get('cop', '') + r.get('ar', '')): continue
            if red and not role: r['kind'] = 'rubric'
            rows.append(r)
    for r in rows:
        r.pop('_free', None); r.pop('_bottom', None)
        if r.get('kind') == 'text': r.pop('kind')
    return rows


def clean(rows):
    out = []
    for r in rows:
        # a paragraph carried over from the previous page: join it to the paragraph it continues
        if r.pop('_pagestart', False) and out and not out[-1].get('kind') and \
                (not r.get('ar') or not r.get('en') or r.get('en', 'A')[:1].islower()):
            for k in ('en', 'cop', 'ar'):
                if r.get(k): out[-1][k] = join_lines([out[-1].get(k, ''), r[k]])
            continue
        for k in ('en', 'ar'):
            if k in r and not re.search(r'[A-Za-z\u0600-\u06FF\u2C80-\u2CFF]', r[k]): del r[k]
        if r.get('en'): r['en'] = re.sub(r'(\S)\s*:\s*:$', r'\1:', r['en'])
        m = re.search(r'\b(\d+) (\d+)$', r.get('en', ''))
        if m and m.group(1) == m.group(2) and r.get('ar') and m.group(1) not in r['ar']:   # "Psalm 116 116": the second number is the Arabic one
            r['en'] = r['en'][:m.start(2)].rstrip(); r['ar'] = r['ar'] + ' ' + m.group(1)
        if not any(r.get(k) for k in ('en', 'cop', 'ar')) and r.get('kind') != 'role': continue
        if r.get('kind') in ('heading', 'rubric'):
            en = (r.get('en') or '').strip()
            role, rest = role_of(en)
            if role and not re.sub(r'[\s:]', '', rest):
                r = {'kind': 'role', 'role': role}
            elif not re.search(r'[A-Za-z\u0600-\u06FF\u2C80-\u2CFF]', en + (r.get('ar') or '')):
                continue
            elif r['kind'] == 'heading' and en[:1].islower():
                r['kind'] = 'rubric'
        # a role row followed by nothing, or two role rows in a row: keep the last
        if r.get('kind') == 'role' and out and out[-1].get('kind') == 'role': out[-1] = r; continue
        # merge a heading's Arabic line that came as a separate heading row
        if r.get('kind') == 'heading' and out and out[-1].get('kind') == 'heading' and not out[-1].get('ar') and r.get('ar') and not r.get('en'):
            out[-1]['ar'] = r['ar']; continue
        out.append(r)
    return out


def main(pdf_path, out_path, prefix, *parts):
    pdf = pdfplumber.open(pdf_path)
    allrows = []   # (page, row)
    for pno, page in enumerate(pdf.pages, 1):
        rows = page_rows(page)
        first = next((r for r in rows if not r.get('kind')), None)
        if first is not None and rows and rows[0] is first: first['_pagestart'] = True
        for r in rows:
            allrows.append((pno, r))
    secs = []
    spec = [p.split('|') for p in parts]
    for k, (title, first, ar) in enumerate(spec):
        a = int(first); b = int(spec[k + 1][1]) if k + 1 < len(spec) else 10 ** 6
        rows = clean([r for p, r in allrows if a <= p < b])
        secs.append({'id': f'{prefix}-{k + 1}', 'title': {'en': title, 'ar': ar}, 'rows': rows})
    json.dump({'source': pdf_path.split('/')[-1], 'sections': secs}, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    for s in secs:
        rs = s['rows']
        print(s['id'], len(rs), 'rows', sum(1 for r in rs if r.get('cop')), 'cop', sum(1 for r in rs if r.get('ar')), 'ar',
              sum(1 for r in rs if r.get('kind') == 'heading'), 'headings', sum(1 for r in rs if r.get('kind') == 'role'), 'roles')


if __name__ == '__main__':
    main(*sys.argv[1:])
