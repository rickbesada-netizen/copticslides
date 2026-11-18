"""Full OCR of Pascha pages using XY-cut segmentation + tesserocr.
usage: python pascha_run.py START END STEP OFFSET
"""
import sys, os, json, re
sys.path.insert(0, '/home/claude/scripts')
import numpy as np
from PIL import Image
import tesserocr
from tesserocr import PyTessBaseAPI, PSM, RIL
from wordfreq import zipf_frequency
import pascha_seg as S

TD = '/home/claude/tess/td'
OUT = '/home/claude/work/ocr2'; os.makedirs(OUT, exist_ok=True)
COP = '/home/claude/work/coptic'; os.makedirs(COP, exist_ok=True)

api_e = PyTessBaseAPI(path=TD, lang='eng', psm=PSM.SINGLE_BLOCK)
api_E = PyTessBaseAPI(path=TD, lang='engbest', psm=PSM.SINGLE_BLOCK)
api_A = PyTessBaseAPI(path=TD, lang='ara', psm=PSM.SINGLE_BLOCK)
for a in (api_e, api_E, api_A):
    a.SetVariable('user_defined_dpi', '300')


def ocr_text_lines(api, img, psm):
    api.SetPageSegMode(psm)
    api.SetImage(img)
    txt = api.GetUTF8Text()
    conf = api.MeanTextConf()
    return [dict(text=l.strip(), conf=float(conf), box=None) for l in txt.split('\n') if l.strip()]


def ocr_lines(api, img, psm):
    if api is api_A:
        return ocr_text_lines(api, img, psm)
    api.SetPageSegMode(psm)
    api.SetImage(img)
    api.Recognize()
    ri = api.GetIterator()
    lines = []
    if ri is None:
        return lines
    level = RIL.TEXTLINE
    while True:
        try:
            t = ri.GetUTF8Text(level)
            c = ri.Confidence(level)
            bb = ri.BoundingBox(level)
        except RuntimeError:
            t = None
        if t and t.strip():
            lines.append(dict(text=t.strip(), conf=round(c, 1), box=bb))
        if not ri.Next(level):
            break
    return lines


def eng_score(text):
    ws = [re.sub(r'[^A-Za-z]', '', w) for w in text.split()]
    ws = [w for w in ws if len(w) >= 2]
    if not ws:
        return 0.0, 0
    good = sum(1 for w in ws if zipf_frequency(w.lower(), 'en') > 2.5)
    return good / len(ws), len(ws)


def ar_ratio(text):
    a = sum(1 for c in text if '؀' <= c <= 'ۿ')
    l = sum(1 for c in text if c.isalpha())
    return a / l if l else 0


def classify_ocr(pno, img, cell, idx):
    h = cell['box'][3] - cell['box'][1]
    psm = PSM.SINGLE_BLOCK if h > 75 else PSM.SINGLE_LINE
    el = ocr_lines(api_e, img, psm)
    etext = ' '.join(l['text'] for l in el)
    econf = (sum(l['conf'] for l in el) / len(el)) if el else 0
    es, nw = eng_score(etext)
    if nw and es >= 0.6 and econf >= 55:
        cell['script'] = 'en'
    else:
        al = ocr_lines(api_A, img, psm)
        atext = ' '.join(l['text'] for l in al)
        aconf = (sum(l['conf'] for l in al) / len(al)) if al else 0
        if al and ar_ratio(atext) > 0.7 and aconf >= 50:
            cell['script'] = 'ar'; cell['lines'] = al; cell['conf'] = round(aconf, 1)
            return
        if nw and es >= 0.45 and econf >= 45:
            cell['script'] = 'en'
        elif re.fullmatch(r'[\d\s().:,\-]+', etext.strip() or 'x') and econf > 60:
            cell['script'] = 'num'; cell['lines'] = el; return
        else:
            cell['script'] = 'cop'
            cell['scores'] = dict(econf=round(econf, 1), es=round(es, 2), aconf=round(aconf, 1))
            out = f'{COP}/p{pno:03d}_{idx:02d}.png'
            img.point(lambda v: 255 if v > 128 else 0).convert('1').save(out, optimize=True)
            cell['img'] = os.path.basename(out)
            return
    El = ocr_lines(api_E, img, psm)
    cell['lines'] = El
    cell['conf'] = round((sum(l['conf'] for l in El) / len(El)) if El else 0, 1)


def strip_tree(node):
    return node


def process(pno):
    work, cells, hcut, tree = S.segment(pno)
    im = Image.fromarray(work)
    W, H = im.size
    for i, c in enumerate(cells):
        x0, y0, x1, y1 = c['box']
        pad = 8
        crop = im.crop((max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)))
        c['id'] = i
        try:
            classify_ocr(pno, crop, c, i)
        except Exception as e:
            c['script'] = 'err'; c['err'] = str(e)
    json.dump(dict(page=pno, W=W, H=H, hcut=int(hcut), tree=tree), open(f'{OUT}/p{pno:03d}.json', 'w'), ensure_ascii=False,
              default=lambda o: int(o) if isinstance(o, (np.integer,)) else str(o))


if __name__ == '__main__':
    a, b, step, off = map(int, sys.argv[1:5])
    for p in range(a + off, b + 1, step):
        if os.path.exists(f'{OUT}/p{p:03d}.json'):
            continue
        try:
            process(p)
            print('done', p, flush=True)
        except Exception as e:
            print('ERR', p, repr(e), flush=True)
