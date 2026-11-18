"""Coptic OCR for the Pascha book print: kNN glyph classifier trained from labelled clusters."""
import sys, os, json, glob, pickle, re
sys.path.insert(0, '/home/claude/scripts')
import numpy as np
import copglyph as G
from sklearn.neighbors import KNeighborsClassifier

LABELS = {
    22: 'ⲙ', 5: 'ⲓ', 20: 'ⲧ', 139: 'ⲁ', 12: 'ⲁ', 16: 'ⲟ', 73: 'ⲡ', 6: 'ⲱ', 34: 'ⲣ', 148: 'ⲉ', 27: 'ⲩ', 174: 'ⲉ', 132: 'ⲩ', 0: 'ϫ',
    28: 'ϥ', 31: 'ⲉ', 123: 'ⲓ', 3: 'ⲉ', 111: 'ⲛ', 128: 'ⲛ', 100: 'ⲟ', 7: 'ⲛ', 102: 'ⲟ', 90: 'ⲟ', 32: 'ⲥ', 19: 'ϩ', 106: 'ⲏ', 64: 'ⲛ',
    76: ':', 85: 'ⲉ', 41: 'ⲏ', 47: 'ⲃ', 61: 'ⲕ', 54: 'ⲛ', 72: 'ⲥ', 117: 'ϣ', 86: 'ⲛ',
    70: 'ⲑ', 42: 'ϯ', 29: 'ⲉ', 43: 'ϧ', 21: 'ⲗ', 57: 'ⲫ', 44: 'ϩ', 48: 'ⲉ', 163: 'ⲗ', 136: 'ⲥ', 8: 'ⲛ', 168: 'ⲇ', 67: 'ⲅ',
    134: 'ⲭ', 81: 'ⲉ', 91: 'ⲟ', 37: 'ⲩ', 146: 'ⲙ', 80: 'ⲙ', 30: 'ⲣ', 156: 'ⲟⲥ', 108: 'ⲧ', 129: 'ϥ', 99: 'ϭ', 138: 'ϩ', 36: 'ϣ',
    39: 'ⲇ', 114: 'ϧ', 101: 'Ⲡ',
    # junk / Arabic / latin clusters (reject class)
    89: '#', 13: '#', 137: '#', 141: '#', 109: '#', 50: '#', 66: '#', 75: '#', 126: '#', 154: '#', 103: '#', 63: '#',
}
MODEL = '/home/claude/work/copknn.pkl'


def train():
    d = pickle.load(open('/home/claude/work/copkm.pkl', 'rb'))
    km, X = d['km'], d['X']
    lab = km.labels_
    Xs, ys = [], []
    for i, l in enumerate(lab):
        if l in LABELS:
            # keep only members close to their centroid (purity)
            Xs.append(X[i]); ys.append(LABELS[l])
    Xs = np.array(Xs)
    knn = KNeighborsClassifier(n_neighbors=5, weights='distance').fit(Xs, ys)
    # per-letter typical relative height (for capital detection)
    hts = {}
    for x, y in zip(Xs, ys):
        hts.setdefault(y, []).append(x[-5] / 3.0)
    typ = {k: float(np.median(v)) for k, v in hts.items()}
    pickle.dump(dict(knn=knn, typ=typ), open(MODEL, 'wb'))
    print('trained', len(ys), 'samples', len(set(ys)), 'classes')


def upper(ch):
    c = ord(ch[0])
    if 0x2C81 <= c <= 0x2CE3 and c % 2 == 1:
        return chr(c - 1) + ch[1:]
    if 0x03E3 <= c <= 0x03EF and c % 2 == 1:
        return chr(c - 1) + ch[1:]
    return ch


_M = None


def read_crop(path):
    global _M
    if _M is None:
        _M = pickle.load(open(MODEL, 'rb'))
    knn, typ = _M['knn'], _M['typ']
    ink = G.load(path)
    if ink.mean() > 0.33:
        return None, 0.0
    out_lines = []
    total = 0; rejected = 0
    for L in G.glyphs(ink):
        xh, base, top = L['xh'], L['base'], L['top']
        if xh < 9:
            continue
        bases, marks = [], []
        for c in L['comps']:
            bottom = c['y'] + c['h']
            fill = c['area'] / max(1, c['w'] * c['h'])
            cy = c['y'] + c['h'] / 2
            small_round = c['h'] < xh * 0.7 and c['w'] < xh * 0.75 and fill > 0.45 and 0.5 < c['w'] / max(1, c['h']) < 2.0
            if small_round and cy > base - xh * 0.4:
                c['ch'] = '.'; bases.append(c)          # dot on the baseline
            elif small_round and cy >= top - xh * 0.05:
                c['ch'] = '·'; bases.append(c)          # upper dot of the colon
            elif bottom < top + xh * 0.2 and c['h'] < xh * 0.6:
                marks.append(c)          # jenkim / overline above the letters
            else:
                bases.append(c)
        todo = [c for c in bases if 'ch' not in c]
        if todo:
            F = np.array([G.feat(c, xh, base) for c in todo])
            pr = knn.predict(F)
            dist, _ = knn.kneighbors(F, n_neighbors=1)
            for c, p, dd in zip(todo, pr, dist[:, 0]):
                total += 1
                if p == '#' or dd > 6.5:
                    c['ch'] = '?'; rejected += 1
                else:
                    if p not in (':', '.', 'ⲟⲥ', 'Ⲡ') and c['h'] / xh > typ.get(p, 1.0) * 1.28:
                        p = upper(p)
                    c['ch'] = p
        # merge vertically stacked dots into ':'
        bases.sort(key=lambda c: c['x'])
        merged = []
        for c in bases:
            if merged and {c['ch'], merged[-1]['ch']} <= {'.', '·'} and abs(c['x'] - merged[-1]['x']) < xh * 0.35:
                merged[-1]['ch'] = ':'; continue
            merged.append(c)
        merged = [c for c in merged if c['ch'] != '·']
        # attach marks
        for m in marks:
            cx = m['x'] + m['w'] / 2
            wide = m['w'] > xh * 0.9
            for c in merged:
                if wide:
                    if c['x'] + c['w'] > m['x'] and c['x'] < m['x'] + m['w'] and c['ch'] not in '.:':
                        c['over'] = True
                elif c['x'] - xh * 0.15 <= cx <= c['x'] + c['w'] + xh * 0.15:
                    c['jen'] = True; break
        s = ''
        prev = None
        for c in merged:
            if prev is not None and c['x'] - (prev['x'] + prev['w']) > xh * 0.42:
                s += ' '
            ch = c['ch']
            if c.get('jen') and ch not in '.:?·':
                ch = ch[0] + '̀' + ch[1:]
            if c.get('over') and ch not in '.:?':
                ch = ''.join(x + '̅' for x in ch)
            s += ch
            prev = c
        s = re.sub(r' ?: ?', ' : ', s).replace(' .', '.').strip()
        if s:
            out_lines.append(s)
    conf = 1 - rejected / total if total else 0
    return '\n'.join(out_lines), conf


if __name__ == '__main__':
    if sys.argv[1] == 'train':
        train()
    elif sys.argv[1] == 'all':
        res = {}
        files = sorted(glob.glob('/home/claude/work/coptic/*.png'))
        for f in files:
            t, conf = read_crop(f)
            if not t or conf < 0.8:
                continue
            lines = t.split('\n')
            good = [l for l in lines if l.count('?') < 2 and not re.search(r'[^\s:.]{22,}', l)]
            if len(good) < max(1, 0.8 * len(lines)):
                continue
            t = '\n'.join(good)
            if len(re.findall('[\u2c80-\u2cff\u03e2-\u03ef]', t)) >= 3:
                res[os.path.basename(f)[:-4]] = t
        json.dump(res, open('/home/claude/work/coptic_text.json', 'w'), ensure_ascii=False)
        print('read', len(res), 'of', len(files))
    else:
        for f in sys.argv[1:]:
            print(f, read_crop(f))
