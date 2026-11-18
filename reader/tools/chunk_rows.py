"""Split long rows into slide-sized rows (like the Resurrection PowerPoint)."""
import json, math, re, sys, glob

TEXT_KEYS = ['en', 'ar', 'ar_ph', 'en_ph', 'cop', 'cop_lat', 'ar_lat']
LIMIT = {'en': 420, 'ar': 380, 'ar_ph': 380, 'en_ph': 420, 'cop': 420, 'cop_lat': 420, 'ar_lat': 420}
BREAK_RE = re.compile(r'(?<=[.!?;:،؛])\s+|\n')


def split_text(t, n):
    if n <= 1 or not t:
        return [t] + [''] * (n - 1)
    # candidate break positions (after sentence punctuation), fallback to spaces
    cands = [m.end() for m in BREAK_RE.finditer(t)]
    spaces = [m.end() for m in re.finditer(r'\s+', t)]
    L = len(t)
    cuts = []
    for k in range(1, n):
        target = L * k / n
        pool = [c for c in cands if (not cuts or c > cuts[-1] + 20) and abs(c - target) < L / n * 0.45]
        if not pool:
            pool = [c for c in spaces if (not cuts or c > cuts[-1] + 10)]
        if not pool:
            break
        cuts.append(min(pool, key=lambda c: abs(c - target)))
    parts = []
    prev = 0
    for c in cuts + [L]:
        parts.append(t[prev:c].strip()); prev = c
    while len(parts) < n:
        parts.append('')
    return parts


def chunk_row(r):
    if r.get('kind') in ('heading', 'role') or r.get('img'):
        return [r]
    n = 1
    for k in TEXT_KEYS:
        if r.get(k):
            n = max(n, math.ceil(len(r[k]) / LIMIT[k]))
    imgs = r.get('cop_img') or []
    if n <= 1:
        return [r]
    n = min(n, 12)
    parts = [dict() for _ in range(n)]
    for k, v in r.items():
        if k in TEXT_KEYS and isinstance(v, str):
            if k == 'cop' and r.get('cop_img'):
                ls = v.split('\n'); m = len(ls)
                for i in range(n):
                    parts[i][k] = '\n'.join(ls[i * m // n:(i + 1) * m // n])
            else:
                for i, piece in enumerate(split_text(v, n)):
                    parts[i][k] = piece
        elif k == 'cop_img':
            m = len(imgs)
            for i in range(n):
                parts[i]['cop_img'] = imgs[i * m // n:(i + 1) * m // n]
        else:
            for p in parts:
                p[k] = v
    out = []
    for i, p in enumerate(parts):
        p = {k: v for k, v in p.items() if v not in ('', [], None)}
        if i > 0 and p.get('kind') == 'heading':
            p.pop('kind')
        if any(k in p for k in TEXT_KEYS + ['cop_img']):
            out.append(p)
    return out or [r]


def process_file(path):
    d = json.load(open(path))
    if 'sections' not in d:
        return None
    before = after = 0
    for s in d['sections']:
        new = []
        for r in s['rows']:
            before += 1
            new += chunk_row(r)
        s['rows'] = new
        after += len(new)
    json.dump(d, open(path, 'w'), ensure_ascii=False)
    return before, after


if __name__ == '__main__':
    for f in sys.argv[1:]:
        print(f, process_file(f))
