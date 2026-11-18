"""Rite/Service of the Deacon (St Demiana & St Athanasius, Sydney) -> app JSON.
Columns: English | Arabic in English letters | Coptic in English letters | Coptic (Athanasius font)
"""
import sys, re, json, collections
sys.path.insert(0, '/home/claude/scripts')
import pdfplumber
from wordfreq import zipf_frequency
from coptic_fonts import convert, POST_OVERLINE

POST_OVERLINE['Athanasius'] = set('/?=')
SRC = '/home/claude/src/deacon.pdf'
OUT = '/home/claude/app/data/deacon.json'

PARTS = ['The Offering of Incense', 'Seasonal Doxologies', 'Doxologies', 'The Third Hour Agpia Prayer', 'The Sixth Hour Agpia Prayer',
         'The Liturgy of Saint Basil', 'Fractions', 'Holy Communion Hymns', 'The Liturgy of Saint Gregory', 'The Liturgy of Saint Cyril',
         'The Rite of Betrothal', 'The Rite of Matrimony', 'Extra Reconciliation Prayers', 'Seasonal Responses', 'Glorification (Tamgeed)', 'Appendices']
ROLE_RE = re.compile(r'^\s*(PRIEST|DEACON|CONGREGATION|PEOPLE|READER|ALL|BISHOP|CHORUS|CANTOR)S?\s*:?\s*(\(.*\))?\s*\*?\s*:?$', re.I)


def is_cop(f):
    return 'Athanasius' in f or 'Avva' in f


def page_part(p):
    ws = [w for w in p.extract_words(extra_attrs=['fontname', 'size']) if w['top'] < 30 and 'Verdana' in w['fontname']]
    t = ' '.join(w['text'] for w in ws).replace('Service of the Deacon', '').strip()
    for part in PARTS:
        if part.lower() in t.lower():
            return part
    return None


def words(p):
    out = []
    for w in p.extract_words(extra_attrs=['fontname', 'size'], x_tolerance=1.5, keep_blank_chars=False):
        f = w['fontname'].split('+')[-1]
        if 'Verdana' in f or 'Wingdings' in f:
            continue
        if w['top'] < 28 or w['bottom'] > p.height - 22:
            continue
        cop = is_cop(f)
        t = w['text']
        if cop:
            fk = 'Athanasius' if 'Athanasius' in f else 'Avva_Shenouda'
            t = convert(t.replace('~', ''), fk)
        out.append(dict(t=t, x0=w['x0'], x1=w['x1'], top=w['top'], bottom=w['bottom'], cop=cop,
                        bold='Bold' in f, ital='Italic' in f, size=w['size'], raw=w['text']))
    return out


def lines_of(ws):
    ws = sorted(ws, key=lambda w: (round(w['top']), w['x0']))
    lines = []
    for w in ws:
        if lines and abs(w['top'] - lines[-1][0]['top']) < 2.5:
            lines[-1].append(w)
        else:
            lines.append([w])
    for l in lines:
        l.sort(key=lambda w: w['x0'])
    return lines


def blocks_of(lines):
    blocks = []
    for l in lines:
        top = min(w['top'] for w in l)
        if blocks:
            prev_bottom = max(w['bottom'] for w in blocks[-1][-1])
            if top - prev_bottom < 5.5:
                blocks[-1].append(l); continue
        blocks.append([l])
    return blocks


def columns_of(block, W):
    ws = [w for l in block for w in l]
    cov = [0] * (int(W) + 2)
    for w in ws:
        for x in range(int(w['x0']), int(w['x1']) + 1):
            cov[x] += 1
    cols = []
    s = None
    gap = 0
    for x, v in enumerate(cov):
        if v:
            if s is None: s = x
            last = x; gap = 0
        elif s is not None:
            gap += 1
            if gap >= 6:
                cols.append((s, last)); s = None
    if s is not None:
        cols.append((s, last))
    return cols


def gutters_of(block, W, minw):
    ws = [w for l in block for w in l]
    if not ws:
        return []
    cov = [0] * (int(W) + 3)
    for w in ws:
        for x in range(int(w['x0']), int(w['x1']) + 1):
            cov[x] = 1
    lo = int(min(w['x0'] for w in ws)); hi = int(max(w['x1'] for w in ws))
    out = []; s = None
    for x in range(lo, hi + 1):
        if not cov[x]:
            if s is None: s = x
        elif s is not None:
            if x - s >= minw: out.append((s, x))
            s = None
    return out


def page_template(ws):
    s4 = sum(1 for w in ws if any(a <= w['x0'] <= a + 9 for a in (105, 185, 265)))
    s3 = sum(1 for w in ws if any(a <= w['x0'] <= a + 9 for a in (130, 240)))
    if s4 >= 6 and s4 >= s3 * 0.8:
        return [107, 187, 267]
    if s3 >= 4:
        return [132, 242]
    return None


def col_text(ws, cop=False):
    lines = lines_of(ws)
    out = ''
    for l in lines:
        t = ' '.join(w['t'] for w in l)
        if out.endswith('-') and not cop:
            out = out[:-1] + t
        else:
            out = (out + ' ' + t) if out else t
    out = re.sub(r'\s+', ' ', out).strip()
    if cop:
        out = re.sub(r'\s*:\s*', ' : ', out).replace(' : ', ': ').replace(' .', '.')
    return out


ARLAT_HINT = re.compile(r"\b(al|wa|ya|el|fi|ala|bel|lana|ellah|allah|yarab|yarabu|erham|anna|haza|kol|men|ela|alayna|abana|salam)\b|['’‘]", re.I)
COPLAT_HINT = re.compile(r"\b(ente|nem|khen|ni|pi|evol|ethouab|epchois|epchoise|owoh|nan|je|emmos|ere|shere|tenti|eti)\b", re.I)


def classify_latin(texts):
    """given latin column texts (left->right after English), label as ar_lat / cop_lat"""
    labels = []
    for t in texts:
        a = len(ARLAT_HINT.findall(t)); c = len(COPLAT_HINT.findall(t))
        labels.append('ar_lat' if a > c else 'cop_lat')
    return labels


def build():
    pdf = pdfplumber.open(SRC)
    docs = collections.OrderedDict()
    cur_part = None
    PREV_CANDS = []
    for pi, p in enumerate(pdf.pages):
        if pi < 8:
            continue
        part = page_part(p) or cur_part
        if part is None:
            continue
        if part == 'Appendices':
            break
        cur_part = part
        doc = docs.setdefault(part, [])
        ws = words(p)
        if not ws:
            continue
        TPL = page_template(ws)
        all_blocks = blocks_of(lines_of(ws))
        big = [b for b in all_blocks if len(b) >= 3 and len(gutters_of(b, p.width, 5)) >= 1]
        page_gut = gutters_of(big[0], p.width, 5) if big else None
        last_gut = None
        CANDS = [gutters_of(b, p.width, 5) for b in all_blocks if len(b) >= 3] + PREV_CANDS + [[(104, 108), (184, 188), (264, 268)], [(130, 133), (240, 243)], [(179, 189)]]
        PREV_CANDS[:] = [gutters_of(b, p.width, 5) for b in all_blocks if len(b) >= 3]
        # title page (big Verdana bold) -> skip (already part title)
        for block in blocks_of(lines_of(ws)):
            bws = [w for l in block for w in l]
            text_all = ' '.join(w['t'] for w in bws).strip()
            if not text_all:
                continue
            # role marker
            if len(block) == 1 and all(w['bold'] for w in bws if not w['cop']) and ROLE_RE.match(' '.join(w['raw'] for w in bws if not w['cop'])):
                m = ROLE_RE.match(' '.join(w['raw'] for w in bws if not w['cop']))
                role = m.group(1).upper()
                role = {'CONGREGATION': 'PEOPLE', 'CHORUS': 'PEOPLE', 'CANTOR': 'PEOPLE'}.get(role, role)
                doc.append(dict(kind='role', role=role)); continue
            # heading: bold, short, not coptic
            latin = [w for w in bws if not w['cop']]
            if latin and all(w['bold'] for w in latin) and len(block) <= 3 and len(text_all) < 120 and not any(w['cop'] for w in bws):
                doc.append(dict(kind='heading', en=re.sub(r'\s+', ' ', ' '.join(w['raw'] for w in latin)).strip(), page=pi + 1)); continue
            gut = gutters_of(block, p.width, 5)
            own = gutters_of(block, p.width, 2)
            def fits(c):
                return all(any(o[0] <= g[0] + 2 and o[1] >= g[1] - 2 for o in own) for g in c)
            cands = [c for c in CANDS if c and fits(c)]
            best = max(cands, key=len) if cands else []
            if len(block) < 3 or len(best) > len(gut):
                gut = best
            bounds = [(a + b) / 2 for a, b in gut]
            colws = [[] for _ in range(len(bounds) + 1)]
            for w in bws:
                k = sum(1 for b in bounds if (w['x0'] + w['x1']) / 2 >= b)
                colws[k].append(w)
            colws = [c for c in colws if c]
            row = dict(page=pi + 1)
            latin_cols = []
            for cw in colws:
                if sum(1 for w in cw if w['cop']) > len(cw) / 2:
                    row['cop'] = ((row.get('cop', '') + ' ') if 'cop' in row else '') + col_text(cw, cop=True)
                else:
                    latin_cols.append(cw)
            if latin_cols:
                row['en'] = col_text(latin_cols[0])
                if all(w['ital'] for w in latin_cols[0]) and len(latin_cols) == 1 and 'cop' not in row:
                    row['kind'] = 'rubric'
                rest = [col_text(c) for c in latin_cols[1:]]
                if len(rest) == 2:
                    row['ar_lat'], row['cop_lat'] = rest
                elif len(rest) == 1:
                    lab = 'cop_lat' if 'cop' in row else classify_latin(rest)[0]
                    row[lab] = rest[0]
                elif len(rest) > 2:
                    row['ar_lat'] = rest[0]; row['cop_lat'] = ' '.join(rest[1:])
            if row.get('en') and 'cop_lat' not in row:
                wsx = re.findall(r'[A-Za-z]{3,}', row['en'])
                if len(wsx) >= 4 and sum(zipf_frequency(w.lower(), 'en') > 3.3 for w in wsx) / len(wsx) < 0.45:
                    row['cop_lat' if 'cop' in row else 'ar_lat'] = row.pop('en')
            if len(row) > 1:
                doc.append(row)
    return docs


SUB = {
    'The Offering of Incense': ('Offering of Incense (Vespers & Matins)', 'رفع بخور عشية وباكر'),
    'Doxologies': ('Doxologies', 'الذكصولوجيات'),
    'Seasonal Doxologies': ('Seasonal Doxologies', 'ذكصولوجيات المناسبات'),
    'The Third Hour Agpia Prayer': ('Third Hour (Liturgy)', 'الساعة الثالثة'),
    'The Sixth Hour Agpia Prayer': ('Sixth Hour (Liturgy)', 'الساعة السادسة'),
    'The Liturgy of Saint Basil': ('Liturgy of St Basil', 'القداس الباسيلي'),
    'Fractions': ('Fractions', 'القسمات'),
    'Holy Communion Hymns': ('Holy Communion & Seasonal Hymns', 'مدائح التوزيع'),
    'The Liturgy of Saint Gregory': ('Liturgy of St Gregory', 'القداس الغريغوري'),
    'The Liturgy of Saint Cyril': ('Liturgy of St Cyril', 'القداس الكيرلسي'),
    'The Rite of Betrothal': ('Rite of Betrothal', 'صلاة الخطوبة'),
    'The Rite of Matrimony': ('Rite of Matrimony', 'صلاة الإكليل'),
    'Extra Reconciliation Prayers': ('Extra Reconciliation Prayers', 'صلوات صلح إضافية'),
    'Seasonal Responses': ('Seasonal Responses', 'مردات المناسبات'),
    'Glorification (Tamgeed)': ('Glorification (Tamgeed)', 'التماجيد'),
}

if __name__ == '__main__':
    docs = build()
    out = dict(source='The Service of the Deacon (St Demiana & St Athanasius Coptic Orthodox Church, Sydney)', sections=[])
    for part, rows in docs.items():
        en, ar = SUB.get(part, (part, part))
        sid = 'dc-' + re.sub(r'[^a-z]+', '-', en.lower()).strip('-')
        out['sections'].append(dict(id=sid, title=dict(en=en, ar=ar), rows=rows))
    json.dump(out, open(OUT, 'w'), ensure_ascii=False)
    for s in out['sections']:
        print(s['id'], len(s['rows']), sum(1 for r in s['rows'] if r.get('kind') == 'heading'))
