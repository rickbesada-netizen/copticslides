"""Assemble OCR output of the Pascha book into app JSON (one file per group)."""
import json, os, re, sys, shutil
sys.path.insert(0, '/home/claude/scripts')
from pascha_toc import GROUPS, OFFSET, LAST_BOOK_PAGE

OCR = '/home/claude/work/ocr2'
COPSRC = '/home/claude/work/coptic'
APP = '/home/claude/app'
OUT = f'{APP}/data/pascha'
IMGOUT = f'{APP}/img/cop'
os.makedirs(OUT, exist_ok=True); os.makedirs(IMGOUT, exist_ok=True)
COPTEXT = {}
if os.path.exists('/home/claude/work/coptic_text.json'):
    COPTEXT = {k: re.sub(r'[ \t]+', ' ', re.sub(r'\?+', '', v)).strip() for k, v in json.load(open('/home/claude/work/coptic_text.json')).items()}
RECLASS = {}
if os.path.exists('/home/claude/work/reclass.json'):
    RECLASS = json.load(open('/home/claude/work/reclass.json'))


def clean_lines(cell):
    lines = [l for l in cell.get('lines', []) if l['text'].strip()]
    lines = [l for l in lines if not (l['conf'] < 35 and len(l['text']) < 8)]
    return lines


def join_en(lines):
    s = ''
    for l in lines:
        t = l['text'].strip()
        t = t.replace('|', 'I') if re.fullmatch(r'\|', t) else t.replace(' | ', ' ').strip('| ')
        if s.endswith('-') and not s.endswith(' -') and t[:1].islower():
            s = s[:-1] + t
        else:
            s = (s + ' ' + t) if s else t
    s = re.sub(r'\s+([,.;:!?])', r'\1', s)
    s = s.replace('“', '"').replace('”', '"').replace("’", "'").replace('—-', '—')
    return s.strip()


def join_ar(lines):
    s = ' '.join(l['text'].strip().strip('|').strip() for l in lines)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s+([.،:؛])', r'\1', s)
    return s.strip()


def cell_info(cell, pno):
    sc = cell.get('script')
    key = f"p{pno:03d}_{cell.get('id', 0):02d}"
    if sc == 'cop' and key in RECLASS:
        r = RECLASS[key]
        if r['script'] in ('drop',):
            return None
        sc = r['script']; cell = dict(cell, lines=r.get('lines', []))
    x0, y0, x1, y1 = cell['box']
    info = dict(script=sc, x0=x0, x1=x1, y0=y0, y1=y1, inverted=cell.get('inverted', False))
    if sc == 'en':
        info['text'] = join_en(clean_lines(cell))
    elif sc in ('ar',):
        info['text'] = join_ar(clean_lines(cell))
    elif sc == 'num':
        info['text'] = join_en(cell.get('lines', []))
    elif sc == 'cop':
        if (y1 - y0) < 22 or (x1 - x0) < 22:
            return None
        info['img'] = cell.get('img')
        if cell.get('img') and cell['img'][:-4] in COPTEXT:
            info['text'] = COPTEXT[cell['img'][:-4]]
    else:
        return None
    if sc != 'cop' and not info.get('text'):
        return None
    return info


def cells_of(node, pno):
    if node is None:
        return []
    if node['t'] == 'cell':
        c = cell_info(node, pno)
        return [c] if c else []
    out = []
    for k in node['kids']:
        out += cells_of(k, pno)
    return out


def make_row(columns, W):
    """columns: list (left->right) of lists of cell infos."""
    # collapse each column into (script -> parts)
    cols = []
    for cl in columns:
        if not cl:
            continue
        scripts = [c['script'] for c in cl if c['script'] != 'num']
        sc = max(set(scripts), key=scripts.count) if scripts else 'num'
        cols.append(dict(script=sc, cells=cl, x0=min(c['x0'] for c in cl), x1=max(c['x1'] for c in cl)))
    # merge neighbours with the same script when the gap is small (over-split columns)
    merged = []
    for c in cols:
        if merged and merged[-1]['script'] == c['script'] and c['x0'] - merged[-1]['x1'] < (45 if c['script'] == 'ar' else 140):
            merged[-1]['cells'] += c['cells']; merged[-1]['x1'] = c['x1']
        else:
            merged.append(c)
    row = {}
    ars = [c for c in merged if c['script'] == 'ar']
    for c in merged:
        cells = sorted(c['cells'], key=lambda q: (q['y0'], q['x0']))
        if c['script'] == 'ar' and ars and c is not ars[-1]:
            key = 'ar_ph'
        else:
            key = c['script']
        if key == 'cop':
            imgs = [q['img'] for q in cells if q.get('img')]
            txt = [q['text'] for q in cells if q.get('text')]
            if imgs:
                row.setdefault('cop_img', []).extend('img/cop/' + i for i in imgs)
            if txt and len(txt) == len(imgs):
                row['cop'] = (row.get('cop', '') + '\n' + '\n'.join(txt)).strip()
                row['cop_ocr'] = 1
            continue
        if key == 'num':
            key = 'en' if (c['x0'] + c['x1']) / 2 < W / 2 else 'ar'
        parts = [q['text'] for q in cells if q.get('text')]
        if key in row:
            parts = [row[key]] + parts
        out = ''
        for part in parts:
            if not out:
                out = part
            elif re.search(r'[.!?:;"\'”)\]،؛۔]\s*$', out) or re.match(r'^\s*[(+]', part) or re.match(r'^(Psalms?|Matthew|Mark|Luke|John|Acts|Romans|Isaiah|Genesis)\b', part):
                out += '\n' + part
            else:
                out += ' ' + part
        row[key] = out
    if all(c.get('inverted') for col in merged for c in col['cells']):
        row['kind'] = 'heading'
    return row


def rows_of(node, pno, W):
    if node is None:
        return []
    if node['t'] == 'cell':
        c = cell_info(node, pno)
        if not c:
            return []
        r = make_row([[c]], W)
        return [r] if r else []
    if node['t'] == 'seq':
        out = []
        for k in node['kids']:
            out += rows_of(k, pno, W)
        return out
    # row node: if every kid is a seq with the same number of parts, zip them into aligned rows
    kids = [k for k in node['kids'] if k]
    if len(kids) > 1 and all(k['t'] == 'seq' for k in kids) and len({len(k['kids']) for k in kids}) == 1:
        out = []
        for parts in zip(*[k['kids'] for k in kids]):
            r = make_row([cells_of(p, pno) for p in parts], W)
            if r:
                out.append(r)
        return out
    r = make_row([cells_of(k, pno) for k in kids], W)
    return [r] if r else []


RUBRIC_RE = re.compile(r'^\s*[+*]|\b(The priest|The deacon|The congregation|Then the|The people|is said|are said|is read|is prayed|says:|say:|sing|chant)\b', re.I)
HEAD_RE = re.compile(r'^(The (Psalm|Gospel|Prophecies|Exposition|Response|Pauline|Catholic|Acts|Praxis|Synaxarium|Litany)|Psalms? \d|Matthew \d|Mark \d|Luke \d|John \d|From the|A reading|Genesis|Exodus|Isaiah|Jeremiah|Ezekiel|Daniel|Hosea|Amos|Micah|Joel|Zechariah|Zephaniah|Proverbs|Job|Wisdom|Sirach|Deuteronomy|Numbers|Leviticus|\(\s*\d+\s*\)$)', re.I)


def classify(row):
    en = row.get('en', '')
    if row.get('kind'):
        return
    first = en.split('\n')[0] if en else ''
    if en and RUBRIC_RE.search(first) and len(en) < 400 and not row.get('cop_img'):
        row['kind'] = 'rubric'
    elif en and len(en) < 70 and '\n' not in en and not en.rstrip().endswith(('.', ',', ';')) and not row.get('cop_img') and len(row.get('ar', '')) < 90:
        row['kind'] = 'heading'
    elif not en and row.get('ar') and len(row['ar']) < 50 and not row.get('cop_img'):
        row['kind'] = 'heading'


def page_rows(pno):
    f = f'{OCR}/p{pno:03d}.json'
    if not os.path.exists(f):
        return None
    d = json.load(open(f))
    rows = rows_of(d['tree'], pno, d['W'])
    for r in rows:
        r['page'] = pno - OFFSET
        classify(r)
    return rows


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower())


def build():
    # global ordered list of section starts
    starts = []
    for g in GROUPS:
        for (bp, en, ar, key) in g['sections']:
            starts.append((bp, g['id'], en, ar, key))
    starts.sort(key=lambda x: x[0])
    # adjust hour starts using running page headers (TOC numbers are sometimes one page off)
    HD = json.load(open('/home/claude/work/headers.json')) if os.path.exists('/home/claude/work/headers.json') else {}
    def hdr(b):
        return HD.get(str(b + OFFSET), '')
    adj = []
    for i, (bp, gid, en, ar, key) in enumerate(starts):
        m = re.match(r'(First|Third|Sixth|Ninth|Eleventh|Twelfth) Hour', key)
        nb = bp
        if m:
            word = m.group(1)
            lo = max(bp - 3, (adj[-1][0] + 1) if adj else bp - 3)
            for b in range(lo, bp + 2):
                if word in hdr(b) and 'Hour' in hdr(b) and word not in hdr(b - 1):
                    nb = b; break
        adj.append((nb, gid, en, ar, key))
    changed = [(a[0], b[0], a[2]) for a, b in zip(starts, adj) if a[0] != b[0]]
    print('header-adjusted starts:', changed)
    starts = sorted(adj, key=lambda x: x[0])
    START_OF = {(g, e): b for (b, g, e, a, k) in starts}
    sec_rows = {}
    missing = []
    cache = {}
    for i, (bp, gid, en, ar, key) in enumerate(starts):
        end_bp = starts[i + 1][0] if i + 1 < len(starts) else LAST_BOOK_PAGE + 1
        rows = []
        for b in range(bp, end_bp + 1):
            p = b + OFFSET
            if p not in cache:
                cache[p] = page_rows(p)
            pr = cache[p]
            if pr is None:
                missing.append(p); continue
            if b == end_bp:
                # next section starts on this page: take rows before its title
                nkey = norm(starts[i + 1][4]) if i + 1 < len(starts) else None
                cut = None
                if nkey:
                    for k, r in enumerate(pr):
                        if nkey and nkey in norm(r.get('en', '')) and len(r.get('en', '')) < 120:
                            cut = k; break
                if cut is None or i + 1 >= len(starts):
                    continue
                rows += pr[:cut]
            elif b == bp and i > 0:
                skey = norm(key)
                cut = 0
                for k, r in enumerate(pr):
                    if skey in norm(r.get('en', '')) and len(r.get('en', '')) < 120:
                        cut = k; break
                rows += pr[cut:]
            else:
                rows += pr
        sec_rows[(gid, bp)] = rows
    # write per group
    index_groups = []
    used_imgs = set()
    for g in GROUPS:
        secs = []
        for (bp0, en, ar, key) in g['sections']:
            bp = START_OF[(g['id'], en)]
            sid = f"{g['id']}-{bp0}"
            rows = sec_rows.get((g['id'], bp), [])
            for r in rows:
                for im in r.get('cop_img', []):
                    used_imgs.add(im.split('/')[-1])
            secs.append(dict(id=sid, title=dict(en=en, ar=ar), page=bp, rows=rows))
        fn = f"pascha/{g['id']}.json"
        json.dump(dict(sections=secs), open(f'{APP}/data/{fn}', 'w'), ensure_ascii=False)
        index_groups.append(dict(id=g['id'], holy=g['holy'], title=dict(en=g['en'], ar=g['ar']),
                                 sections=[dict(id=s['id'], title=s['title'], file=fn, page=s['page']) for s in secs]))
    json.dump(dict(groups=index_groups), open(f'{OUT}/index.json', 'w'), ensure_ascii=False)
    for im in used_imgs:
        src = f'{COPSRC}/{im}'
        if os.path.exists(src) and not os.path.exists(f'{IMGOUT}/{im}'):
            shutil.copy(src, f'{IMGOUT}/{im}')
    print('missing pages', len(set(missing)), 'images', len(used_imgs))
    print('rows per group', {g['id']: sum(len(sec_rows.get((g['id'], START_OF[(g['id'], s[1])]), [])) for s in g['sections']) for g in GROUPS})


if __name__ == '__main__':
    build()
