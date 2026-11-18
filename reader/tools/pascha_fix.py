"""Fix-up passes over OCR output.
mode ar  : re-OCR Arabic cells with full-text call (fixes RTL iterator bug)
mode cop : re-test cells classified Coptic (missed Arabic / English, decorations)
usage: python pascha_fix.py MODE START END STEP OFF
"""
import sys, os, json, re
sys.path.insert(0, '/home/claude/scripts')
import numpy as np
from PIL import Image
from tesserocr import PyTessBaseAPI, PSM
from wordfreq import zipf_frequency
import pascha_seg as S

TD = '/home/claude/tess/td'
OCR = '/home/claude/work/ocr2'
A = PyTessBaseAPI(path=TD, lang='ara', psm=PSM.SINGLE_BLOCK); A.SetVariable('user_defined_dpi', '300')
E = PyTessBaseAPI(path=TD, lang='engbest', psm=PSM.SINGLE_BLOCK); E.SetVariable('user_defined_dpi', '300')


def full(api, img, psm):
    api.SetPageSegMode(psm); api.SetImage(img)
    txt = api.GetUTF8Text(); conf = api.MeanTextConf()
    return [dict(text=l.strip(), conf=float(conf), box=None) for l in txt.split('\n') if l.strip()], conf


def walk(n):
    if n is None: return
    if n['t'] == 'cell': yield n
    else:
        for k in n['kids']: yield from walk(k)


def eng_score(text):
    ws = [re.sub(r'[^A-Za-z]', '', w) for w in text.split()]
    ws = [w for w in ws if len(w) >= 2]
    if not ws: return 0.0
    return sum(1 for w in ws if zipf_frequency(w.lower(), 'en') > 2.5) / len(ws)


def ar_ratio(t):
    a = sum(1 for c in t if '؀' <= c <= 'ۿ'); l = sum(1 for c in t if c.isalpha())
    return a / l if l else 0


def process(p, mode):
    f = f'{OCR}/p{p:03d}.json'
    if not os.path.exists(f): return False
    d = json.load(open(f))
    if d.get('fixed_' + mode): return False
    work, cells, hcut, tree = S.segment(p)
    im = Image.fromarray(work); W, H = im.size
    for c in walk(d['tree']):
        sc = c.get('script')
        if (mode == 'ar' and sc != 'ar') or (mode == 'cop' and sc != 'cop'):
            continue
        x0, y0, x1, y1 = c['box']
        crop = im.crop((max(0, x0 - 8), max(0, y0 - 8), min(W, x1 + 8), min(H, y1 + 8)))
        psm = PSM.SINGLE_BLOCK if (y1 - y0) > 75 else PSM.SINGLE_LINE
        if mode == 'ar':
            c['lines'], c['conf'] = full(A, crop, psm)
        else:
            a = np.array(crop) < 128
            ink = a.mean()
            # decorations: very dense or extreme shapes
            if ink > 0.33 or (y1 - y0) < 24:
                c['script'] = 'drop'; continue
            al, ac = full(A, crop, psm)
            at = ' '.join(l['text'] for l in al)
            nar = len(re.findall(r'[ء-ي]{2,}', at))
            if al and ar_ratio(at) > 0.8 and ac >= 35 and nar >= 1:
                c['script'] = 'ar'; c['lines'] = al; c['conf'] = ac; c['was'] = 'cop'; continue
            el, ec = full(E, crop, psm)
            et = ' '.join(l['text'] for l in el)
            if eng_score(et) >= 0.5 and ec >= 45:
                c['script'] = 'en'; c['lines'] = el; c['conf'] = ec; c['was'] = 'cop'; continue
    d['fixed_' + mode] = True
    json.dump(d, open(f, 'w'), ensure_ascii=False)
    return True


if __name__ == '__main__':
    mode = sys.argv[1]
    a, b, step, off = map(int, sys.argv[2:6])
    for p in range(a + off, b + 1, step):
        try:
            if process(p, mode): print('fixed', mode, p, flush=True)
        except Exception as e:
            print('ERR', p, repr(e), flush=True)
