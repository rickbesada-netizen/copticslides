"""Glyph segmentation + features for the Pascha book's Coptic print."""
import numpy as np, cv2
from PIL import Image

N = 20  # feature bitmap size


def load(path):
    a = np.array(Image.open(path).convert('L')) < 128
    return a.astype(np.uint8)


def lines_of(ink):
    """Split crop into text lines by horizontal projection; returns list of (y0,y1)."""
    prof = ink.sum(1)
    on = prof > 0
    runs = []
    s = None
    for i, v in enumerate(on):
        if v and s is None: s = i
        if not v and s is not None: runs.append([s, i]); s = None
    if s is not None: runs.append([s, len(on)])
    if not runs: return []
    # merge tiny runs (jenkims, overlines) into the line below them
    hs = [b - a for a, b in runs]
    med = np.median([h for h in hs if h > 8] or [20])
    out = []
    pend = None
    for a, b in runs:
        if b - a < med * 0.45:
            # small run: attach to next line if close, else previous
            if pend is None: pend = [a, b]
            else: pend[1] = b
            continue
        if pend is not None and a - pend[1] < med * 0.6:
            a = pend[0]
        elif pend is not None and out:
            out[-1][1] = pend[1]
        pend = None
        out.append([a, b])
    if pend is not None and out:
        out[-1][1] = pend[1]
    return [tuple(x) for x in out]


def glyphs(ink):
    """Yield lines -> list of components with geometry."""
    res = []
    for (y0, y1) in lines_of(ink):
        sub = ink[y0:y1]
        n, lab, st, _ = cv2.connectedComponentsWithStats(sub, connectivity=8)
        comps = []
        for i in range(1, n):
            x, y, w, h, area = st[i]
            if area < 4: continue
            comps.append(dict(x=int(x), y=int(y + y0), w=int(w), h=int(h), area=int(area), bmp=(lab[y:y + h, x:x + w] == i).astype(np.uint8)))
        if not comps: continue
        # line metrics from "body" components
        bodies = [c for c in comps if c['h'] > 6 and c['w'] > 3]
        if not bodies: continue
        hs = np.array([c['h'] for c in bodies])
        xh = float(np.median(hs))
        base = float(np.median([c['y'] + c['h'] for c in bodies if abs(c['h'] - xh) < xh * 0.25] or [y1]))
        top = base - xh
        res.append(dict(y0=y0, y1=y1, xh=xh, base=base, top=top, comps=sorted(comps, key=lambda c: c['x'])))
    return res


def feat(c, xh, base):
    b = c['bmp']
    h, w = b.shape
    s = max(h, w)
    pad = np.zeros((s, s), np.uint8)
    pad[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = b
    small = cv2.resize(pad * 255, (N, N), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    geo = np.array([h / xh, w / xh, (base - (c['y'] + h)) / xh, (base - c['y']) / xh, c['area'] / (h * w)], np.float32)
    return np.concatenate([small.ravel(), geo * 3.0])
