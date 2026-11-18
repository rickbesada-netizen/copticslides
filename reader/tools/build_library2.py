"""Library v2: Coptic Reader-style content library (categories -> groups -> documents)."""
import json, glob, re, os
D = '/home/claude/app/data'
FILES = ['resurrection.json', 'agpeya.json', 'deacon.json'] + sorted(f[len(D) + 1:] for f in glob.glob(f'{D}/pascha/*.json') if not f.endswith('index.json'))

ROLE_WORDS = {'priest': 'PRIEST', 'the priest': 'PRIEST', 'deacon': 'DEACON', 'the deacon': 'DEACON', 'people': 'PEOPLE',
              'the people': 'PEOPLE', 'congregation': 'PEOPLE', 'the congregation': 'PEOPLE', 'reader': 'READER', 'all': 'ALL'}
AR_ROLES = {'الكاهن': 'PRIEST', 'الشماس': 'DEACON', 'الشعب': 'PEOPLE', 'القارئ': 'READER'}

docs = {}
for f in FILES:
    d = json.load(open(f'{D}/{f}'))
    changed = False
    for s in d['sections']:
        heads = []
        for i, r in enumerate(s['rows']):
            en = (r.get('en') or '').strip().rstrip(':').strip().lower()
            ar = (r.get('ar') or '').strip().rstrip(':').strip()
            if r.get('kind') != 'role' and not r.get('cop_img') and not r.get('cop') and (en in ROLE_WORDS or (not en and ar in AR_ROLES)) and len(r.get('ar', '')) < 15:
                r.clear(); r.update(kind='role', role=ROLE_WORDS.get(en) or AR_ROLES.get(ar)); changed = True
            if r.get('kind') == 'heading':
                t = (r.get('en') or r.get('ar') or '').strip()
                if t and len(t) < 90:
                    heads.append([i, t])
        docs[s['id']] = dict(file=f, title=s['title'], heads=heads[:120])
    if changed:
        json.dump(d, open(f'{D}/{f}', 'w'), ensure_ascii=False)


def doc(i):
    assert i in docs, i
    return {'doc': i}


def grp(en, ar, items, holy=None, open_=False):
    g = {'group': {'en': en, 'ar': ar}, 'items': items}
    if holy: g['holy'] = holy
    if open_: g['open'] = True
    return g


def ids(prefix):
    return [k for k in docs if k.startswith(prefix)]


pascha_groups = json.load(open(f'{D}/pascha/index.json'))['groups']
HOLY_ORDER = ['last-friday', 'lazarus', 'palm', 'every-hour', 'monday-eve', 'monday', 'tuesday-eve', 'tuesday', 'wednesday-eve', 'wednesday',
              'thursday-eve', 'thursday', 'friday-eve', 'friday', 'psalms', 'saturday', 'easter-eve']
pg = {g['id']: g for g in pascha_groups}
holy_week = [grp(pg[k]['title']['en'], pg[k]['title']['ar'], [doc(s['id']) for s in pg[k]['sections']], holy=pg[k].get('holy')) for k in HOLY_ORDER]

res_eve = [doc(x) for x in ['res-2', 'res-19', 'res-34', 'res-39', 'res-51', 'res-87', 'res-93']]
res_dox = [doc(x) for x in ['res-103', 'res-120', 'res-152', 'res-161', 'res-172', 'res-177']]
res_lit = [doc(x) for x in ['res-192', 'res-203', 'res-217', 'res-241', 'res-267', 'res-280', 'res-288', 'res-292', 'res-301', 'res-320',
                            'res-333', 'res-348', 'res-355', 'res-368', 'res-380', 'res-385', 'res-417', 'res-431', 'res-458']]

CATS = [
    dict(id='agpeya', title={'en': 'Agpeya', 'ar': 'الأجبية'}, items=[
        doc('ag-intro'), doc('ag-prime'), doc('ag-terce'), doc('ag-sext'), doc('ag-none'), doc('ag-vespers'), doc('ag-compline'),
        doc('ag-veil'), doc('ag-midnight'), doc('ag-absolution'), doc('ag-selected'), doc('ag-psindex'),
        grp('Hours before the Liturgy (with Coptic)', 'ساعات ما قبل القداس (بالقبطي)', [doc('dc-third-hour-liturgy'), doc('dc-sixth-hour-liturgy')])]),
    dict(id='psalmody', title={'en': 'Psalmody', 'ar': 'التسبحة'}, items=[
        grp('Doxologies', 'الذكصولوجيات', [doc('dc-doxologies'), doc('dc-seasonal-doxologies'), doc('res-103'), doc('res-120')], open_=True),
        grp('Praises', 'التسابيح', [doc('saturday-517'), doc('res-51'), doc('res-19'), doc('res-87')], open_=True)]),
    dict(id='bible', title={'en': 'Bible', 'ar': 'الكتاب المقدس'}, items=[
        doc('psalms-449'), doc('saturday-579'), {'special': 'scripture-index', 'title': {'en': 'Scripture Readings Index', 'ar': 'فهرس القراءات'}}]),
    dict(id='liturgies', title={'en': 'Liturgies', 'ar': 'القداسات'}, items=[
        doc('dc-offering-of-incense-vespers-matins'),
        grp('The Divine Liturgies', 'القداسات الإلهية', [doc('dc-liturgy-of-st-basil'), doc('dc-liturgy-of-st-gregory'), doc('dc-liturgy-of-st-cyril'),
                                                         doc('dc-fractions'), doc('dc-extra-reconciliation-prayers')], open_=True),
        grp('Feast & Holy Week Liturgies', 'قداسات الأعياد والبصخة', [doc('palm-82'), doc('thursday-303'), doc('thursday-321'), doc('saturday-604'),
                                                                     doc('easter-eve-625')] + res_lit)]),
    dict(id='readings', title={'en': 'Readings', 'ar': 'القراءات'}, items=[
        {'special': 'occasion-readings', 'title': {'en': 'Readings for the selected day', 'ar': 'قراءات اليوم المختار'}}] + holy_week + [
        grp('Feast of the Resurrection', 'عيد القيامة', [doc('res-172'), doc('res-267'), doc('res-280'), doc('res-292'), doc('res-355'), doc('res-368')])]),
    dict(id='melodies', title={'en': 'Melodies', 'ar': 'الألحان'}, items=[
        doc('dc-holy-communion-seasonal-hymns'), doc('dc-seasonal-responses'), doc('dc-glorification-tamgeed'),
        grp('Feast of the Resurrection', 'عيد القيامة', [doc('res-288'), doc('res-301'), doc('res-320'), doc('res-333'), doc('res-380'), doc('res-385'), doc('res-417')])]),
    dict(id='index', title={'en': 'Index', 'ar': 'الفهرس'}, items=[{'special': 'index', 'title': {'en': 'Index', 'ar': 'الفهرس'}}]),
    dict(id='clergy', title={'en': 'Clergy', 'ar': 'الإكليروس'}, items=[
        doc('last-friday-22'), doc('dc-rite-of-betrothal'), doc('dc-rite-of-matrimony'), doc('palm-95'), doc('thursday-303')]),
    dict(id='special', title={'en': 'Special', 'ar': 'المناسبات'}, items=[
        grp('Holy Pascha (Holy Week)', 'البصخة المقدسة', holy_week, open_=True),
        grp('Feast of the Resurrection', 'عيد القيامة المجيد', [grp('Eve of the Feast: Evening Incense', 'عشية العيد', res_eve, holy='easter'),
                                                                grp('Doxologies and Matins', 'الذكصولوجيات وباكر', res_dox),
                                                                grp('The Holy Liturgy of the Feast', 'قداس العيد', res_lit)])]),
]

json.dump(dict(version=2, docs=docs, categories=CATS), open(f'{D}/library.json', 'w'), ensure_ascii=False)
print('docs', len(docs), 'library.json', os.path.getsize(f'{D}/library.json'))
