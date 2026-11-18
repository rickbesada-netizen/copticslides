"""AGPIA (C.O.P.T. Sydney, NKJV) -> app JSON. Pages are printed two-up with crop marks."""
import re, json, collections
import pdfplumber

SRC = '/home/claude/src/agpia.pdf'
OUT = '/home/claude/app/data/agpeya.json'


def halves(p):
    W = p.width
    for (x0, x1) in ((0, W / 2), (W / 2, W)):
        yield p.crop((x0, 0, x1, p.height))


def lines(crop):
    chars = [c for c in crop.chars if c['text'].strip() or c['text'] == ' ']
    words = crop.extract_words(extra_attrs=['fontname', 'size'], x_tolerance=1.5, keep_blank_chars=False)
    words = [w for w in words if w['text'] not in ('Cut', 'here', 'FINAL')]
    ls = []
    for w in sorted(words, key=lambda w: (round(w['top']), w['x0'])):
        if ls and abs(w['top'] - ls[-1]['top']) < 2.5:
            ls[-1]['words'].append(w)
        else:
            ls.append(dict(top=w['top'], words=[w]))
    out = []
    for l in ls:
        ws = sorted(l['words'], key=lambda w: w['x0'])
        t = ' '.join(w['text'] for w in ws)
        fonts = [w['fontname'] for w in ws]
        out.append(dict(t=t, top=l['top'], bottom=max(w['bottom'] for w in ws), x0=ws[0]['x0'], x1=ws[-1]['x1'],
                        bold=sum('Bold' in f for f in fonts) > len(fonts) / 2,
                        ital=sum('Italic' in f for f in fonts) > len(fonts) / 2,
                        size=max(w['size'] for w in ws)))
    return out


def build():
    pdf = pdfplumber.open(SRC)
    pages = []
    for pi, p in enumerate(pdf.pages):
        for h in halves(p):
            ls = lines(h)
            if not ls:
                continue
            # body region: between the crop marks (text block). header = first italic small line
            body = [l for l in ls if 60 < l['top'] < p.height - 60 and l['size'] >= 7 and not re.fullmatch(r'(C|Cu|Cut|ut|t|here|he|ere|re|e|Cut here)', l['t'].strip())]
            if not body:
                continue
            header = None
            if body and body[0]['ital'] and body[0]['size'] < 9.5:
                header = body[0]['t']; body = body[1:]
            # page number: last short numeric line
            if body and re.fullmatch(r'[0-9ivxlc]+', body[-1]['t'].strip()):
                body = body[:-1]
            pages.append(dict(pdf=pi + 1, header=header, lines=body))
    return pages


def to_docs(pages):
    docs = collections.OrderedDict()
    cur = None
    for pg in pages:
        h = pg['header'] or cur
        if h is None:
            continue
        cur = h
        docs.setdefault(h, []).append(pg)
    out = []
    for h, pgs in docs.items():
        rows = []
        para = None
        left = None
        for pg in pgs:
            ls = pg['lines']
            if not ls:
                continue
            lm = min(l['x0'] for l in ls)
            for l in ls:
                t = l['t']
                indent = l['x0'] - lm
                is_head = (l['bold'] or (t.isupper() and len(t) > 5)) and (t.isupper() or re.match(r'^(PSALM|THE|LITANY|GOSPEL|ABSOLUTION|TRISAGION)', t)) and not l['ital']
                if is_head:
                    if para: rows.append(para); para = None
                    if rows and rows[-1].get('kind') == 'heading' and rows[-1].get('_pdf') == pg['pdf'] and len(rows[-1]['en']) < 60:
                        rows[-1]['en'] += ' ' + t
                    else:
                        rows.append(dict(kind='heading', en=t, _pdf=pg['pdf']))
                    continue
                kind = 'rubric' if l['ital'] else None
                newpara = para is None or (para.get('kind') != kind) or indent > 6 or (l['top'] - para['_bottom'] > l['size'] * 0.9 and para['_pdf'] == pg['pdf'])
                if newpara:
                    if para: rows.append(para)
                    para = dict(en=t, _bottom=l['bottom'], _pdf=pg['pdf'])
                    if kind: para['kind'] = kind
                else:
                    if para['en'].endswith('-'):
                        para['en'] = para['en'][:-1] + t
                    else:
                        para['en'] += ' ' + t
                    para['_bottom'] = l['bottom']; para['_pdf'] = pg['pdf']
        if para: rows.append(para)
        for r in rows:
            r.pop('_bottom', None); r.pop('_pdf', None)
            r['en'] = re.sub(r'\s+', ' ', r['en']).strip()
        out.append((h, rows))
    return out


if __name__ == '__main__':
    pages = build()
    docs = to_docs(pages)
    for h, rows in docs:
        print(repr(h), len(rows), [r['en'][:40] for r in rows[:3]])
    json.dump([dict(header=h, rows=rows) for h, rows in docs], open('/home/claude/work/agpeya_raw.json', 'w'), ensure_ascii=False)
