import sys, json, os
sys.path.insert(0, '/home/claude/scripts')
import numpy as np
from PIL import Image
from tesserocr import PyTessBaseAPI, PSM
import pascha_seg as S
api = PyTessBaseAPI(path='/home/claude/tess/td', lang='engbest', psm=PSM.SPARSE_TEXT)
out = {}
for p in range(14, 652):
    try:
        a, ink = S.load(p)
        hc = S.find_header_cut(ink)
        im = Image.fromarray(a[:hc + 10, int(a.shape[1] * 0.12):int(a.shape[1] * 0.62)])
        api.SetImage(im)
        out[p] = ' '.join(api.GetUTF8Text().split())
    except Exception as e:
        out[p] = ''
json.dump(out, open('/home/claude/work/headers.json', 'w'), indent=0)
print('done')
