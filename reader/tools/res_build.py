import json, re, os, subprocess
from wordfreq import zipf_frequency

def fix_ar_spaces(t):
    toks = t.split(' ')
    out = []
    for tok in toks:
        if out:
            a = out[-1]
            j = a + tok
            za = zipf_frequency(a, 'ar'); zb = zipf_frequency(tok, 'ar'); zj = zipf_frequency(j, 'ar')
            if re.fullmatch(r'[\u0621-\u064a]+', a) and re.fullmatch(r'[\u0621-\u064a]+[^\s]*', tok) and zj >= 2.0 and (min(za, zb) < 1.0 or len(tok) == 1 or zj > max(za, zb) + 1.5 or (zj >= 3.0 and zj >= max(za, zb) - 0.5 and min(za, zb) < 3.0)):
                out[-1] = j; continue
        out.append(tok)
    return ' '.join(out)

from PIL import Image

P = json.load(open('/home/claude/work/res_runs.json'))
OUT = '/home/claude/app/data'
IMG = '/home/claude/app/img/res'
os.makedirs(OUT, exist_ok=True); os.makedirs(IMG, exist_ok=True)

# (first_slide, last_slide, english title, arabic title)
SECTIONS = [
    (2, 18, 'Offering of Evening Incense: Prayer of Thanksgiving', 'رفع بخور عشية: صلاة الشكر'),
    (19, 33, 'The Verses of the Cymbals', 'أرباع الناقوس'),
    (34, 38, 'O King of Peace & We Worship You', 'يا ملك السلام ونسجد لك'),
    (39, 50, 'Litanies of the Sick, Travellers and Departed', 'أواشي المرضى والمسافرين والراقدين'),
    (51, 86, 'The Seven Tunes Hymn', 'لحن السبع طرايق'),
    (87, 92, 'Your Mercies O My God', 'مراحمك يا إلهي'),
    (93, 102, 'Litany of the Oblations', 'أوشية القرابين'),
    (103, 119, 'Doxologies: Gloria, Trisagion and Hail to You', 'الذكصولوجيات: تسبحة الملائكة والثلاث تقديسات'),
    (120, 151, 'Doxologies of the Resurrection', 'ذكصولوجيات القيامة'),
    (152, 160, 'Introduction to the Creed and the Orthodox Creed', 'مقدمة قانون الإيمان وقانون الإيمان'),
    (161, 171, 'Litany of the Gospel and Psalm', 'أوشية الإنجيل والمزمور'),
    (172, 176, 'Matins Psalm, Gospel (Mark 16:2-11) and Response', 'مزمور وإنجيل باكر ومرد الإنجيل'),
    (177, 191, 'Conclusion of Matins and Absolution', 'ختام باكر والتحليل'),
    (192, 202, 'The Liturgy: Offering of the Lamb', 'القداس: تقديم الحمل'),
    (203, 216, 'Alleluia, This Is the Day & Blessed Is He', 'هلليلويا هذا هو اليوم'),
    (217, 240, 'Prayer of Thanksgiving and Absolution of the Servants', 'صلاة الشكر وتحليل الخدام'),
    (241, 266, 'Tai Shori and the Intercessions', 'طاي شوري والشفاعات'),
    (267, 279, 'The Pauline Epistle (1 Corinthians 15)', 'البولس'),
    (280, 287, 'The Catholic Epistle (1 Peter 3:15-4:6)', 'الكاثوليكون'),
    (288, 291, 'Praxis Response', 'مرد الإبركسيس'),
    (292, 300, 'The Acts (Acts 2:22-35)', 'الإبركسيس'),
    (301, 319, 'Ya Kol Al Sefoof and the Resurrection Re-enactment', 'يا كل الصفوف وتمثيلية القيامة'),
    (320, 332, 'Procession of the Resurrection', 'دورة عيد القيامة'),
    (333, 347, 'Christ Is Risen and the Joyful Agios', 'المسيح قام وآجيوس الفرايحي'),
    (348, 354, 'Litany of the Gospel', 'أوشية الإنجيل'),
    (355, 367, 'Liturgy Psalm and Psalm Response', 'مزمور القداس ومرد المزمور'),
    (368, 379, 'Liturgy Gospel (John 20:1-18) and Response', 'إنجيل القداس ومرد الإنجيل'),
    (380, 384, 'Aspasmos Watos', 'الأسبسمس الواطس'),
    (385, 416, 'Communion Hymns', 'ألحان التوزيع'),
    (417, 430, 'Hymn for the Resurrection', 'ترنيمة القيامة'),
    (431, 457, 'Conclusion of the Service', 'ختام الصلوات'),
    (458, 460, 'Our Father (Coptic Phonetic)', 'أبانا الذي (قبطي معرب)'),
]


def letters_ratio(t):
    s = re.sub(r'\s', '', t)
    if not s:
        return 0
    return sum(1 for c in s if c.isalpha()) / len(s)


def cluster(vals, gap):
    vals = sorted(vals)
    groups = []
    for v in vals:
        if groups and v - groups[-1][-1] <= gap:
            groups[-1].append(v)
        else:
            groups.append([v])
    return groups


def join_lines(runs, rtl=False):
    runs = sorted(runs, key=lambda r: (round(r['top'] / 6), -r['x1'] if rtl else r['x0']))
    paras = []
    prev = None
    for r in runs:
        if prev is not None and r['top'] - prev['bottom'] > max(prev['size'], r['size']) * 0.9:
            paras.append('\n')
        elif paras:
            paras.append(' ')
        paras.append(r['t'])
        prev = r
    s = ''.join(paras)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r' *\n *', '\n', s).strip()
    return s


NAV = {'Main', 'Back', 'End', 'Main Back', 'Back Main', 'End Back Main'}


def slide_row(p):
    runs = [r for r in p['runs'] if r['t'] not in NAV and not re.fullmatch(r'(Main|Back|End)( (Main|Back|End))*', r['t'])]
    # phonetic lines printed under the English / Arabic text: detect by vocabulary
    def en_ratio(t):
        ws = [w for w in re.findall(r"[A-Za-z']+", t) if len(w) > 2]
        return (sum(1 for w in ws if zipf_frequency(w.lower(), 'en') > 3.3) / len(ws), len(ws)) if ws else (1.0, 0)
    def ar_ratio_(t):
        ws = [w for w in re.findall(r'[\u0621-\u064a]+', t) if len(w) > 1]
        return (sum(1 for w in ws if zipf_frequency(w, 'ar') > 2.0) / len(ws), len(ws)) if ws else (1.0, 0)
    for kind, fn, th, tag in (('lat', en_ratio, 0.62, 'latph'), ('ar', ar_ratio_, 0.68, 'arph')):
        col = sorted([r for r in runs if r['k'] == kind], key=lambda r: r['top'])
        if not col:
            continue
        # group runs into lines, lines into blocks separated by large gaps
        lines = []
        for r in col:
            if lines and abs(r['top'] - lines[-1][0]['top']) < r['size'] * 0.5:
                lines[-1].append(r)
            else:
                lines.append([r])
        blocks = [[lines[0]]]
        for a, b in zip(lines, lines[1:]):
            gap = b[0]['top'] - max(x['bottom'] for x in a)
            if gap > b[0]['size'] * 1.2:
                blocks.append([b])
            else:
                blocks[-1].append(b)
        TL = 0.45 if kind == 'lat' else 0.6
        for bi, blk in enumerate(blocks):
            lt = [' '.join(r['t'] for r in ln) for ln in blk]
            verdict = []
            for t_ in lt:
                ratio, n = fn(t_)
                if kind == 'ar' and re.search('[پچڤگ]', t_): verdict.append(True)
                elif kind == 'lat' and t_.isupper(): verdict.append(False)
                elif n >= 2: verdict.append(ratio < TL)
                else: verdict.append(None)
            split = None
            for k in range(len(lt)):
                suf = [v for v in verdict[k:] if v is not None]
                pre = [v for v in verdict[:k] if v is not None]
                if suf and all(suf) and verdict[k] is not False and (not pre or sum(pre) == 0):
                    split = k; break
            if split is not None:
                for ln in blk[split:]:
                    for r in ln:
                        r['k'] = tag
    latph = [r for r in runs if r['k'] == 'latph']
    arph = [r for r in runs if r['k'] == 'arph']
    lat = [r for r in runs if r['k'] == 'lat']
    cop = [r for r in runs if r['k'] == 'cop']
    ar = [r for r in runs if r['k'] == 'ar']
    alltext = ' '.join(r['t'] for r in runs)
    runs = [dict(r) for r in runs]
    row = {}
    if not runs or letters_ratio(alltext) < 0.55 or len(re.sub(r'[^A-Za-z؀-ۿⲀ-⳿Ϣ-ϯ]', '', alltext)) < 6:
        row['img'] = True
        return row
    # latin columns by x0
    if lat:
        groups = cluster([r['x0'] for r in lat], 110)
        first_max = groups[0][-1] if groups else 0
        en_ = [r for r in lat if r['x0'] <= first_max]
        ph_ = [r for r in lat if r['x0'] > first_max]
        side = bool(en_ and ph_) and min(r['bottom'] for r in ph_) < max(r['bottom'] for r in en_) and max(r['top'] for r in ph_) > min(r['top'] for r in en_) and min(r['x0'] for r in ph_) > max(r['x0'] for r in en_) + 60
        if len(groups) > 1 and side:
            en, ph = en_, ph_
            # phonetic columns sit right of English; English is wide-left
            row['en'] = join_lines(en)
            row['en_ph'] = join_lines(ph)
        else:
            row['en'] = join_lines(lat)
    if latph:
        row['en_ph'] = (row.get('en_ph', '') + '\n' + join_lines(latph)).strip()
    if arph:
        row['ar_ph'] = (row.get('ar_ph', '') + '\n' + join_lines(arph, rtl=True)).strip()
    if cop:
        row['cop'] = join_lines(cop)
    if ar:
        groups = cluster([r['x1'] for r in ar], 110)
        last_min = groups[-1][0] if groups else 0
        a_main = [r for r in ar if r['x1'] >= last_min]; a_other = [r for r in ar if r['x1'] < last_min]
        a_side = bool(a_main and a_other) and min(r['bottom'] for r in a_other) < max(r['bottom'] for r in a_main) and max(r['top'] for r in a_other) > min(r['top'] for r in a_main) and max(r['x1'] for r in a_other) < min(r['x0'] for r in a_main) + 20
        if len(groups) > 1 and a_side:
            row['ar'] = join_lines([r for r in ar if r['x1'] >= last_min], rtl=True)
            row['ar_ph'] = join_lines([r for r in ar if r['x1'] < last_min], rtl=True)
        else:
            row['ar'] = join_lines(ar, rtl=True)
    for k in ('ar', 'ar_ph'):
        if k in row:
            t = re.sub(r'[\u064b-\u0652\u0670]', '', row[k])
            t = re.sub(r'(?<=[\u0621-\u064a]) (?=[\u0621-\u064a]{1}(\s|$))', '', t) if False else t
            row[k] = '\n'.join(fix_ar_spaces(re.sub(r'[ \t]+', ' ', ln).strip()) for ln in t.split('\n'))
    for k in ('en_ph', 'ar_ph', 'en'):
        if k in row and len(re.findall(r'[A-Za-z\u0621-\u064a]', row[k])) < 3:
            del row[k]
    # mostly-punctuation vocal charts -> also give image
    if cop and letters_ratio(row.get('cop', '')) < 0.6:
        row['img'] = True
    return {k: v for k, v in row.items() if v}


def render(slide):
    out = f'{IMG}/s{slide:03d}.webp'
    if os.path.exists(out):
        return
    tmp = f'/home/claude/work/tmp/rs{slide}'
    subprocess.run(['pdftoppm', '-r', '110', '-f', str(slide), '-l', str(slide), '-singlefile', '-png',
                    '/home/claude/src/res.pdf', tmp], check=True)
    Image.open(tmp + '.png').convert('RGB').save(out, 'WEBP', quality=72)
    os.remove(tmp + '.png')


book = dict(id='resurrection', title=dict(en='Feast of the Resurrection', ar='عيد القيامة المجيد', cop='Ⲡⲓϣⲁⲓ ⲛ̀ⲧⲉ ϯⲁ̀ⲛⲁⲥⲧⲁⲥⲓⲥ'),
            source='Ressurrection_Feast_2015.pdf', sections=[])
bypage = {p['page']: p for p in P}
for (a, b, en, arT) in SECTIONS:
    rows = []
    for s in range(a, b + 1):
        r = slide_row(bypage[s])
        r['slide'] = s
        if r.get('img'):
            render(s)
            r['img'] = f'img/res/s{s:03d}.webp'
        if len(r) > 1:
            rows.append(r)
    book['sections'].append(dict(id=f'res-{a}', title=dict(en=en, ar=arT), rows=rows))
json.dump(book, open(f'{OUT}/resurrection.json', 'w'), ensure_ascii=False)
n = sum(len(s['rows']) for s in book['sections'])
imgs = sum(1 for s in book['sections'] for r in s['rows'] if r.get('img'))
print('sections', len(book['sections']), 'rows', n, 'images', imgs)
import subprocess as _sp
_sp.run(['python3', '/home/claude/scripts/fix_coptic_split.py'])
