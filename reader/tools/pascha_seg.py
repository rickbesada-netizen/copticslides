"""Page segmentation for the scanned Pascha book: rows (bands) x columns (cells)."""
import numpy as np
from PIL import Image
import cv2


def load(pno):
    im = Image.open(f'/home/claude/work/pages/p{pno:03d}.png').convert('L')
    a = np.array(im)
    ink = (a < 128).astype(np.uint8)
    return a, ink


def find_header_cut(ink):
    H, W = ink.shape
    top = ink[: int(H * 0.2)]
    rows = top.sum(1)
    # long horizontal rule = row with ink > 60% width
    cands = np.where(rows > 0.55 * W)[0]
    if len(cands):
        # take the last rule row in the first contiguous header area (first rule group)
        y = cands[0]
        # extend through the group
        while y + 1 < len(rows) and rows[y + 1] > 0.3 * W:
            y += 1
        if y < H * 0.2:
            return y + 4
    return int(H * 0.095)


def remove_rules(ink):
    """Erase long horizontal and vertical lines (table borders, rules). Return cleaned ink and inverted-bar mask."""
    H, W = ink.shape
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (150, 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 100))
    hl = cv2.morphologyEx(ink, cv2.MORPH_OPEN, hk)
    vl = cv2.morphologyEx(ink, cv2.MORPH_OPEN, vk)
    clean = ink.copy()
    clean[hl > 0] = 0
    clean[vl > 0] = 0
    return clean, hl, vl


def inverted_bars(a):
    """Find black title bars (white text on black). Return list of (y0,y1,x0,x1)."""
    ink = (a < 128).astype(np.uint8)
    H, W = ink.shape
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (60, 25))
    solid = cv2.morphologyEx(ink, cv2.MORPH_OPEN, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(solid)
    bars = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if w > 250 and h > 45 and area > 0.5 * w * h:
            bars.append((y, y + h, x, x + w))
    return bars


def runs(mask):
    """Return list of (start,end) of True runs."""
    out = []
    s = None
    for i, v in enumerate(mask):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append((s, i)); s = None
    if s is not None:
        out.append((s, len(mask)))
    return out


def segment(pno, gap_row=34):
    a, ink0 = load(pno)
    H, W = ink0.shape
    bars = inverted_bars(a)
    # make a working copy where inverted bars are flipped to normal (white bg, black text)
    work = a.copy()
    for (y0, y1, x0, x1) in bars:
        work[y0:y1, x0:x1] = 255 - work[y0:y1, x0:x1]
    ink = (work < 128).astype(np.uint8)
    hcut = find_header_cut(ink)
    clean, hl, vl = remove_rules(ink)
    # ignore page edges (scan borders)
    mx = int(W * 0.015)
    clean[:, :mx] = 0; clean[:, W - mx:] = 0
    clean[:hcut] = 0
    clean[H - int(H * 0.012):] = 0
    # remove specks
    n, lab, st, _ = cv2.connectedComponentsWithStats(clean)
    small = np.zeros(n, bool)
    small[1:] = st[1:, cv2.CC_STAT_AREA] < 6
    clean[small[lab]] = 0
    vlmask = (cv2.dilate(vl, np.ones((1, 15), np.uint8)) > 0)
    hlrows = hl.sum(1) > 0
    cells = []

    def vcuts(y0, y1, x0, x1):
        sub = clean[y0:y1, x0:x1]
        h = y1 - y0
        colsum = sub.sum(0)
        vr = vlmask[y0:y1, x0:x1].sum(0) > h * 0.25
        if h > 300:
            sm = np.convolve(colsum, np.ones(5) / 5, 'same')
            empty = (sm <= max(2, h * 0.005)) | vr
            g = 10
        else:
            g = 40 if h > 110 else 60
            tol = max(1, int(h * 0.004)) if h > 110 else 0
            empty = (colsum <= tol) | vr
        rs = runs(~empty)
        cols = []
        for s_, e_ in rs:
            if cols and s_ - cols[-1][1] < g and not vr[cols[-1][1]:s_].any():
                cols[-1] = (cols[-1][0], e_)
            else:
                cols.append((s_, e_))
        # merge columns narrower than 110px into neighbours (avoid splitting words)
        merged = []
        for c in cols:
            if merged and (c[1] - c[0] < 110 or merged[-1][1] - merged[-1][0] < 110) and h > 300:
                merged[-1] = (merged[-1][0], c[1])
            else:
                merged.append(c)
        return [(x0 + a, x0 + b) for a, b in merged]

    def hcuts(y0, y1, x0, x1, gap):
        sub = clean[y0:y1, x0:x1]
        rs = runs(sub.sum(1) > 0)
        out = []
        for s_, e_ in rs:
            if out and s_ - out[-1][1] < gap and not hlrows[y0 + out[-1][1]:y0 + s_].any():
                out[-1] = (out[-1][0], e_)
            else:
                out.append((s_, e_))
        return [(y0 + a, y0 + b) for a, b in out]

    def tight(y0, y1, x0, x1):
        sub = clean[y0:y1, x0:x1]
        ys = np.where(sub.sum(1) > 0)[0]; xs = np.where(sub.sum(0) > 0)[0]
        if len(ys) == 0: return None
        return (y0 + ys[0], y0 + ys[-1] + 1, x0 + xs[0], x0 + xs[-1] + 1)

    def cut(y0, y1, x0, x1, depth=0):
        t = tight(y0, y1, x0, x1)
        if t is None: return None
        y0, y1, x0, x1 = t
        if (x1 - x0) < 14 or (y1 - y0) < 14: return None
        if depth < 12:
            rows30 = hcuts(y0, y1, x0, x1, 30)
            if len(rows30) > 1:
                kids = [cut(a, b, x0, x1, depth + 1) for a, b in rows30]
                kids = [k for k in kids if k]
                return dict(t='seq', kids=kids) if len(kids) > 1 else (kids[0] if kids else None)
            cols = vcuts(y0, y1, x0, x1)
            if len(cols) > 1:
                kids = [cut(y0, y1, a, b, depth + 1) for a, b in cols]
                kids = [k for k in kids if k]
                return dict(t='row', kids=kids) if len(kids) > 1 else (kids[0] if kids else None)
            rows8 = hcuts(y0, y1, x0, x1, 7)
            if len(rows8) > 2:
                for k in range(1, min(5, len(rows8) - 1)):
                    ry0 = rows8[k][0]
                    if len(vcuts(ry0, y1, x0, x1)) > 1 and ry0 - y0 < (y1 - y0) * 0.5:
                        kids = [cut(y0, rows8[k - 1][1], x0, x1, depth + 1), cut(ry0, y1, x0, x1, depth + 1)]
                        kids = [q for q in kids if q]
                        return dict(t='seq', kids=kids)
                for k in range(1, min(5, len(rows8) - 1)):
                    ry1 = rows8[-1 - k][1]
                    if len(vcuts(y0, ry1, x0, x1)) > 1 and y1 - ry1 < (y1 - y0) * 0.5:
                        kids = [cut(y0, ry1, x0, x1, depth + 1), cut(rows8[-k][0], y1, x0, x1, depth + 1)]
                        kids = [q for q in kids if q]
                        return dict(t='seq', kids=kids)
            for gap in (30, 16):
                rows_ = hcuts(y0, y1, x0, x1, gap)
                if len(rows_) > 1:
                    kids = [cut(a, b, x0, x1, depth + 1) for a, b in rows_]
                    kids = [k for k in kids if k]
                    return dict(t='seq', kids=kids) if len(kids) > 1 else (kids[0] if kids else None)
        inv = any(by0 - 4 <= y0 and y1 <= by1 + 4 and bx0 - 4 <= x0 and x1 <= bx1 + 4 for (by0, by1, bx0, bx1) in bars)
        c = dict(t='cell', box=(int(x0), int(y0), int(x1), int(y1)), inverted=bool(inv))
        cells.append(c)
        return c

    tree = cut(0, H, 0, W)
    return work, cells, hcut, tree


if __name__ == '__main__':
    import sys
    from PIL import ImageDraw
    for p in sys.argv[1:]:
        p = int(p)
        work, cells, hcut, tree = segment(p)
        im = Image.fromarray(work).convert('RGB'); d = ImageDraw.Draw(im)
        d.line([0, hcut, im.width, hcut], fill=(0, 200, 0), width=6)
        for c in cells:
            d.rectangle(c['box'], outline=(255, 0, 0) if not c['inverted'] else (0, 0, 255), width=7)
        im.resize((im.width // 3, im.height // 3)).save(f'/home/claude/work/chk/seg{p}.png')
        print(p, len(cells))
