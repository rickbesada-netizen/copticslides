"""Library v3: Coptic Reader-style navigation tree (tile grids -> part lists -> documents).
Part documents are slices of a parent document between two headings."""
import json, os, re
D = '/home/claude/app/data'
L = json.load(open(f'{D}/library.json'))  # v2 output (docs + heads)
docs = L['docs']
nodes = {}


def head_idx(doc, kw, nth=0, after=0):
    hits = [i for i, h in docs[doc]['heads'] if kw.lower() in h.lower() and i >= after]
    if len(hits) <= nth:
        raise KeyError(f'{doc}: heading {kw!r} not found')
    return hits[nth]


def part(parent, pid, en, ar, start, end=None):
    did = f'{parent}@{pid}'
    p = docs[parent]
    heads = [[i - start, h] for i, h in p['heads'] if i >= start and (end is None or i < end)]
    docs[did] = dict(file=p['file'], parent=parent, start=start, end=end, title=dict(en=en, ar=ar), heads=heads)
    return did


def leaf(did):
    return {'doc': did}


def node(nid, en, ar, icon, items, view='list'):
    n = dict(id=nid, title=dict(en=en, ar=ar), icon=icon, view=view, items=items)
    nodes[nid] = n
    return {'node': nid}


def special(sid, en, ar, icon):
    return {'special': sid, 'title': dict(en=en, ar=ar), 'icon': icon}


# ---------------- liturgy parts
B = 'dc-liturgy-of-st-basil'
b_word = head_idx(B, '[2] THE READINGS'); b_faith = head_idx(B, '[3] PRAYER OF RECONCILIATION'); b_dist = head_idx(B, '[7] FRACTION')
basil = [part(B, 'lamb', 'Offering of the Lamb', 'تقديم الحمل', 0, b_word), part(B, 'word', 'Liturgy of the Word', 'قداس الكلمة', b_word, b_faith),
         part(B, 'faithful', 'Liturgy of the Faithful', 'قداس المؤمنين', b_faith, b_dist), part(B, 'dist', 'Distribution', 'التوزيع', b_dist)]
G = 'dc-liturgy-of-st-gregory'
g1 = head_idx(G, 'HEAVENLY HYMN'); g2 = head_idx(G, 'ANAMNESIS'); g3 = head_idx(G, 'LITANIES'); g4 = head_idx(G, 'FRACTION & COMMUNION')
gregory = [part(G, 'recon', 'Prayer of Reconciliation', 'صلاة الصلح', 0, g1), part(G, 'anaphora', 'The Anaphora', 'الأنافورا', g1, g2),
           part(G, 'anamnesis', 'Anamnesis & Consecration', 'التذكار والتقديس', g2, g3), part(G, 'litanies', 'Litanies & Commemoration', 'الأواشي والمجمع', g3, g4),
           part(G, 'dist', 'Fraction & Distribution', 'القسمة والتوزيع', g4)]
C = 'dc-liturgy-of-st-cyril'
c1 = head_idx(C, 'ANAPHORA'); c2 = head_idx(C, 'CONSECRATION'); c3 = head_idx(C, 'THE LITANIES'); c4 = head_idx(C, 'COMMEMORATION OF THE SAINTS')
cyril = [part(C, 'recon', 'Prayers of Reconciliation', 'صلوات الصلح', 0, c1), part(C, 'anaphora', 'The Anaphora', 'الأنافورا', c1, c2),
         part(C, 'consecration', 'The Consecration', 'التقديس', c2, c3), part(C, 'litanies', 'The Litanies', 'الأواشي', c3, c4),
         part(C, 'commemoration', 'Commemoration of the Saints', 'المجمع', c4)]
I = 'dc-offering-of-incense-vespers-matins'
i_eve = head_idx(I, 'EVENING & SATURDAY MORNING INCENSE'); i_morn = head_idx(I, 'MORNING INCENSE', after=i_eve + 1); i_glo = head_idx(I, 'THE GLORIA')
i_creed = head_idx(I, 'INTRODUCTION TO THE CREED'); i_maj = head_idx(I, 'THE THREE MAJOR LITANIES'); i_conc = head_idx(I, 'CONCLUDING PRAYER', after=i_maj)
inc_open = part(I, 'open', 'Prayer of Thanksgiving & Verses of the Cymbals', 'صلاة الشكر وأرباع الناقوس', 0, i_eve)
inc_eve = part(I, 'eve', 'Litanies of the Evening Incense', 'أواشي رفع بخور عشية', i_eve, i_morn)
inc_morn = part(I, 'morn', 'Litanies of the Morning Incense', 'أواشي رفع بخور باكر', i_morn, i_glo)
inc_glo = part(I, 'gloria', 'The Gloria, Trisagion & Hail to You', 'تسبحة الملائكة والثلاث تقديسات', i_glo, i_creed)
inc_creed = part(I, 'gospel', 'The Creed, Litany of the Gospel & Gospel', 'قانون الإيمان والإنجيل', i_creed, i_maj)
inc_maj = part(I, 'major', 'The Three Major Litanies', 'الأواشي الكبار', i_maj, i_conc)
inc_conc = part(I, 'conclusion', 'Concluding Prayer', 'ختام الصلاة', i_conc)

vespers = [leaf(inc_open), leaf(inc_eve), leaf(inc_glo), leaf('dc-doxologies'), leaf('dc-seasonal-doxologies'), leaf(inc_creed), leaf(inc_conc)]
matins = [leaf(inc_open), leaf(inc_morn), leaf(inc_glo), leaf('dc-doxologies'), leaf('dc-seasonal-doxologies'), leaf(inc_creed), leaf(inc_maj), leaf(inc_conc)]

# ---------------- Holy Week tree from pascha index
pidx = json.load(open(f'{D}/pascha/index.json'))['groups']
pg = {g['id']: g for g in pidx}
DAY_ORDER = ['last-friday', 'lazarus', 'palm', 'monday-eve', 'monday', 'tuesday-eve', 'tuesday', 'wednesday-eve', 'wednesday', 'thursday-eve', 'thursday',
             'friday-eve', 'friday', 'psalms', 'saturday', 'easter-eve', 'every-hour']
pascha_days = [node('pascha-' + k, pg[k]['title']['en'], pg[k]['title']['ar'], 'pascha', [leaf(s['id']) for s in pg[k]['sections']]) for k in DAY_ORDER]
for k in DAY_ORDER:
    nodes['pascha-' + k]['holy'] = pg[k].get('holy')

res_eve = ['res-2', 'res-19', 'res-34', 'res-39', 'res-51', 'res-87', 'res-93']
res_mat = ['res-103', 'res-120', 'res-152', 'res-161', 'res-172', 'res-177']
res_lit = ['res-192', 'res-203', 'res-217', 'res-241', 'res-267', 'res-280', 'res-288', 'res-292', 'res-301', 'res-320', 'res-333', 'res-348', 'res-355', 'res-368', 'res-380', 'res-385', 'res-417', 'res-431', 'res-458']
resurrection = node('resurrection', 'Feast of the Resurrection', 'عيد القيامة المجيد', 'resurrection', [
    node('res-vespers', 'Eve of the Feast: Vespers', 'عشية العيد', 'vespers', [leaf(x) for x in res_eve]),
    node('res-matins', 'Doxologies & Matins', 'الذكصولوجيات وباكر', 'matins', [leaf(x) for x in res_mat]),
    node('res-liturgy', 'The Holy Liturgy of the Feast', 'قداس العيد', 'liturgy', [leaf(x) for x in res_lit])], view='tiles')
nodes['resurrection']['holy'] = 'easter'

CATS = [
    node('agpeya', 'Agpeya', 'الأجبية', 'agpeya', [leaf(x) for x in ['ag-intro', 'ag-prime', 'ag-terce', 'ag-sext', 'ag-none', 'ag-vespers', 'ag-compline', 'ag-veil',
                                                                  'ag-midnight', 'ag-absolution', 'ag-selected', 'ag-psindex', 'dc-third-hour-liturgy', 'dc-sixth-hour-liturgy']]),
    node('psalmody', 'Psalmody', 'التسبحة', 'psalmody', [
        node('doxologies', 'Doxologies', 'الذكصولوجيات', 'doxology', [leaf('dc-doxologies'), leaf('dc-seasonal-doxologies'), leaf('res-103'), leaf('res-120')]),
        node('praises', 'Praises', 'التسابيح', 'psalmody', [leaf('saturday-517'), leaf('res-51'), leaf('res-87')]),
        node('cymbals', 'Verses of the Cymbals', 'أرباع الناقوس', 'cymbals', [leaf(inc_open), leaf('res-19')])], view='tiles'),
    {'special': 'bible', 'title': dict(en='Bible', ar='الكتاب المقدس'), 'icon': 'bible', 'cat': True},
    node('liturgies', 'Liturgies', 'القداسات', 'liturgies', [
        node('basil', 'St. Basil', 'القداس الباسيلي', 'basil', [leaf(x) for x in basil]),
        node('gregory', 'St. Gregory', 'القداس الغريغوري', 'gregory', [leaf(x) for x in gregory]),
        node('cyril', 'St. Cyril', 'القداس الكيرلسي', 'cyril', [leaf(x) for x in cyril]),
        node('matins', 'Matins', 'باكر', 'matins', matins),
        node('vespers', 'Vespers', 'عشية', 'vespers', vespers),
        node('fractions', 'Fractions', 'القسمات', 'fraction', [leaf('dc-fractions'), leaf('dc-extra-reconciliation-prayers')]),
        node('feast-liturgies', 'Feasts & Holy Week', 'الأعياد والبصخة', 'feast', [leaf('palm-82'), leaf('thursday-303'), leaf('thursday-321'), leaf('saturday-604'), leaf('easter-eve-625'), {'node': 'res-liturgy'}])], view='tiles'),
    node('readings', 'Readings', 'القراءات', 'readings', [
        special('occasion-readings', 'Today', 'اليوم', 'today'),
        node('readings-pascha', 'Holy Pascha', 'البصخة المقدسة', 'pascha', [{'node': 'pascha-' + k} for k in DAY_ORDER if k != 'every-hour']),
        node('readings-res', 'Resurrection', 'القيامة', 'resurrection', [leaf(x) for x in ['res-172', 'res-267', 'res-280', 'res-292', 'res-355', 'res-368']]),
        special('scripture-index', 'Readings Index', 'فهرس القراءات', 'readings')], view='tiles'),
    node('melodies', 'Melodies', 'الألحان', 'melodies', [
        node('communion', 'Communion Hymns', 'مدائح التوزيع', 'communion', [leaf('dc-holy-communion-seasonal-hymns'), leaf('res-385')]),
        node('responses', 'Seasonal Responses', 'مردات المناسبات', 'cymbals', [leaf('dc-seasonal-responses'), leaf('res-288')]),
        node('tamgeed', 'Glorification', 'التماجيد', 'veneration', [leaf('dc-glorification-tamgeed')]),
        node('res-hymns', 'Resurrection Hymns', 'ألحان القيامة', 'resurrection', [leaf(x) for x in ['res-301', 'res-320', 'res-333', 'res-380', 'res-417']])], view='tiles'),
    {'special': 'index', 'title': dict(en='Index', ar='الفهرس'), 'icon': 'index', 'cat': True},
    node('clergy', 'Clergy', 'الإكليروس', 'clergy', [leaf('last-friday-22'), leaf('dc-rite-of-betrothal'), leaf('dc-rite-of-matrimony'), leaf('palm-95'),
                                                   leaf('thursday-303'), leaf('dc-extra-reconciliation-prayers')]),
    node('special', 'Special', 'المناسبات', 'special', [
        node('crowning', 'Crowning', 'الإكليل', 'crowning', [leaf('dc-rite-of-betrothal'), leaf('dc-rite-of-matrimony')]),
        node('unction', 'Unction', 'القنديل', 'unction', [leaf('last-friday-22')]),
        node('funeral', 'Funeral', 'التجنيز', 'funeral', [leaf('palm-95')]),
        node('pascha', 'Pascha', 'البصخة', 'pascha', [{'node': 'pascha-' + k} for k in DAY_ORDER]),
        node('lakkan', 'Lakkan', 'اللقان', 'lakkan', [leaf('thursday-303')]),
        {'node': 'resurrection'},
        node('palm', 'Palm Sunday', 'أحد الشعانين', 'palm', [leaf(s['id']) for s in pg['palm']['sections']]),
        node('lazarus', 'Lazarus Saturday', 'سبت لعازر', 'lazarus', [leaf('lazarus-47')]),
        node('last-friday', 'Last Friday of Lent', 'جمعة ختام الصوم', 'cross', [leaf('last-friday-15'), leaf('last-friday-22')])], view='tiles'),
]
home = [c for c in CATS]
json.dump(dict(version=3, docs=docs, nodes=nodes, home=home), open(f'{D}/library.json', 'w'), ensure_ascii=False)
print('docs', len(docs), 'nodes', len(nodes), os.path.getsize(f'{D}/library.json'))
