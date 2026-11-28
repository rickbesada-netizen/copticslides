"""Register the rite books in data/library.json: Baptism, Laqqan (Epiphany, Covenant Thursday,
Apostles), Feast of the Apostles and the Prostration (Kneeling) prayers. Safe to run again."""
import json, os, re
D = os.path.join(os.path.dirname(__file__), '..', 'data')
L = json.load(open(os.path.join(D, 'library.json'), encoding='utf-8'))


def add_file(fname):
    d = json.load(open(os.path.join(D, fname), encoding='utf-8'))
    for s in d['sections']:
        heads = [[i, r['en'] if r.get('en') else r.get('ar', '')] for i, r in enumerate(s['rows'])
                 if r.get('kind') == 'heading' and (r.get('en') or r.get('ar')) and len(r.get('en', '')) < 90]
        L['docs'][s['id']] = {'file': fname, 'title': s['title'], 'heads': heads}
    return [s['id'] for s in d['sections']]


bap = add_file('baptism.json')
lqe = add_file('laqan-epiphany.json')
apo = add_file('apostles.json')
pro = add_file('prostration.json')

# drop the earlier text-only Baptism index
for k in [k for k in L['docs'] if k.startswith('baptism-source-')]: del L['docs'][k]

N = L['nodes']
N['baptism'] = {'id': 'baptism', 'title': {'en': 'Baptism', 'ar': 'المعمودية'}, 'icon': 'baptism', 'view': 'list',
                'items': [{'doc': d} for d in bap]}
if 'lakkan-thursday' not in N:
    old = N['lakkan']
    N['lakkan-thursday'] = dict(old, id='lakkan-thursday', title={'en': 'Laqqan of Covenant Thursday', 'ar': 'لقان خميس العهد'})
N['lakkan-epiphany'] = {'id': 'lakkan-epiphany', 'title': {'en': 'Laqqan of the Epiphany', 'ar': 'لقان عيد الغطاس'}, 'icon': 'lakkan',
                        'view': 'list', 'items': [{'doc': d} for d in lqe]}
N['lakkan'] = {'id': 'lakkan', 'title': {'en': 'Laqqan', 'ar': 'اللقان'}, 'icon': 'lakkan', 'view': 'list',
               'items': [{'node': 'lakkan-epiphany'}, {'node': 'lakkan-thursday'}, {'doc': apo[2]}]}
L['docs'][apo[2]]['title'] = {'en': 'Laqqan of the Apostles', 'ar': 'لقان عيد الرسل'}
N['apostles'] = {'id': 'apostles', 'title': {'en': 'Feast of the Apostles', 'ar': 'عيد الرسل'}, 'icon': 'apostles', 'view': 'list',
                 'items': [{'doc': d} for d in apo]}
N['prostration'] = {'id': 'prostration', 'title': {'en': 'Prostration (Kneeling)', 'ar': 'السجدة'}, 'icon': 'prostration', 'view': 'list',
                    'items': [{'doc': d} for d in pro]}
sp = N['special']['items']
for nid, after in [('prostration', 'lakkan'), ('apostles', 'prostration')]:
    if not any(x.get('node') == nid for x in sp):
        i = next((k for k, x in enumerate(sp) if x.get('node') == after), len(sp) - 1)
        sp.insert(i + 1, {'node': nid})
json.dump(L, open(os.path.join(D, 'library.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('special:', [x.get('node') for x in sp])
