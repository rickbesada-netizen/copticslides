import json, sys, unicodedata, re, collections
sys.path.insert(0, '/home/claude/scripts')
from coptic_fonts import convert, COPTIC_FONTS
from fontTools.ttLib import TTFont

GO = TTFont('/home/claude/work/font_241.ttf').getGlyphOrder()
AR_FIX = {'ی': 'ي', 'ھ': 'ه', 'ۀ': 'ه', 'ک': 'ك'}

def gid2ar(g, fallback):
    if g == 1127 or g == 752:
        return ''  # kashida
    n = GO[g] if 0 <= g < len(GO) else ''
    if n.startswith('uni'):
        try:
            s = ''.join(chr(int(n[3 + k:7 + k], 16)) for k in range(0, len(n) - 3, 4))
            s = unicodedata.normalize('NFKC', s)
            return ''.join(AR_FIX.get(c, c) for c in s)
        except Exception:
            pass
    return ''.join(AR_FIX.get(c, c) for c in fallback)

ARABIC_CAPABLE_ = ('Times New Roman', 'Arial', 'Helvetica', 'Arabic Transparent', 'Tahoma')

def gid_is_ar(c):
    if not c['f'].startswith(ARABIC_CAPABLE_):
        return False
    g = c['cid']
    if g in (1127, 752):
        return True
    n = GO[g] if 0 <= g < len(GO) else ''
    return n[:5] in ('uni06', 'uniFE', 'uniFB', 'uniFD', 'uniFC') and not n.startswith('uniFEFF')

def is_ar_char(c):
    t = c['t']
    if gid_is_ar(c):
        return True
    return any('؀' <= x <= 'ۿ' or 'ﭐ' <= x <= '﻿' for x in t)

ARABIC_CAPABLE = ('Times New Roman', 'Arial', 'Helvetica', 'Arabic Transparent', 'Tahoma')

def classify(c):
    f = c['f']
    if f in COPTIC_FONTS:
        return 'cop'
    if is_ar_char(c):
        return 'ar'
    if c['t'] == ' ' and c['cid'] == 3 and f.startswith(ARABIC_CAPABLE):
        return 'sp'
    if c['t'].strip() == '':
        return 'sp'
    # arabic digits / punctuation in arabic fonts handled by neighbor
    return 'lat'

def build_lines(cs):
    """Group chars into runs (same script, same line, contiguous)."""
    runs = []
    for c in cs:
        k = classify(c)
        c['k'] = k
    # assign spaces to the script of previous char
    prev = None
    for c in cs:
        if c['k'] == 'sp':
            c['k'] = prev['k'] if prev else 'lat'
            c['space'] = True
        else:
            prev = c
    cur = None
    for c in cs:
        if cur and c['k'] == cur['k'] and abs(c['top'] - cur['top']) < max(4, c['size'] * 0.5) \
                and c['x0'] - cur['x1'] < c['size'] * 3 and cur['x0'] - c['x1'] < c['size'] * 3:
            cur['chars'].append(c)
            cur['x0'] = min(cur['x0'], c['x0']); cur['x1'] = max(cur['x1'], c['x1'])
            cur['bottom'] = max(cur['bottom'], c['bottom'])
        else:
            cur = dict(k=c['k'], chars=[c], x0=c['x0'], x1=c['x1'], top=c['top'], bottom=c['bottom'], size=c['size'])
            runs.append(cur)
    return runs

def run_text(r):
    k = r['k']; cs = r['chars']
    if k == 'cop':
        # split by font segments
        out = []; seg = ''; segf = None
        for c in cs:
            f = c['f'] if c['f'] in COPTIC_FONTS else segf
            if f != segf and seg:
                out.append(convert(seg, segf)); seg = ''
            segf = f or 'CS New Athanasius'
            seg += c['t']
        if seg: out.append(convert(seg, segf))
        s = ''.join(out)
    elif k == 'ar':
        bases = []
        for ci, c in enumerate(cs):
            if c.get('space'):
                bases.append(dict(t=' ', x=(c['x0'] + c['x1']) / 2, marks=''))
                continue
            t = gid2ar(c['cid'], c['t']) if is_ar_char(c) or c['f'].startswith(ARABIC_CAPABLE) else c['t']
            if t and all(unicodedata.category(x) == 'Mn' for x in t) and bases:
                # attach mark to nearest base by x
                cx = (c['x0'] + c['x1']) / 2
                best = min((b for b in bases if b['t'] != ' '), key=lambda b: abs(b['x'] - cx), default=bases[-1])
                best['marks'] += t
                continue
            if t == '':
                continue
            # brackets mirror in visual order
            bases.append(dict(t=t, x=(c['x0'] + c['x1']) / 2, marks=''))
        bases.sort(key=lambda b: -b['x'])
        s = ''.join(b['t'] + b['marks'] for b in bases)
        s = s.replace('(', '\0').replace(')', '(').replace('\0', ')')
    else:
        s = ''.join(c['t'] for c in cs)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def page_runs(cs):
    runs = build_lines(cs)
    out = []
    for r in runs:
        t = run_text(r)
        if not t or re.fullmatch(r'[\s.\-_/:]*', t):
            continue
        out.append(dict(k=r['k'], t=t, x0=round(r['x0'], 1), x1=round(r['x1'], 1), top=round(r['top'], 1),
                        bottom=round(r['bottom'], 1), size=round(r['size'], 1),
                        bold=any('Bold' in c['f'] for c in r['chars']),
                        ital=any('Italic' in c['f'] for c in r['chars']),
                        fonts=sorted(set(c['f'] for c in r['chars']))))
    return out

if __name__ == '__main__':
    R = json.load(open('/home/claude/work/rchars.json'))
    pages = []
    for i, cs in R:
        pages.append(dict(page=i + 1, runs=page_runs(cs)))
    json.dump(pages, open('/home/claude/work/res_runs.json', 'w'), ensure_ascii=False, indent=0)
    with open('/home/claude/work/res_dump.txt', 'w') as f:
        for p in pages:
            f.write(f"\n=== {p['page']}\n")
            for r in sorted(p['runs'], key=lambda r: (r['k'], r['top'])):
                f.write(f"[{r['k']} x{r['x0']:.0f}-{r['x1']:.0f} y{r['top']:.0f} s{r['size']:.0f}] {r['t']}\n")
