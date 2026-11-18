import json, os
D = '/home/claude/app/data'
res = json.load(open(f'{D}/resurrection.json'))
secs = res['sections']
RG = [
    ('Eve of the Feast: Evening Incense', 'عشية العيد: رفع بخور عشية', 0, 7),
    ('Doxologies and Matins', 'الذكصولوجيات وباكر', 7, 13),
    ('The Holy Liturgy of the Feast', 'قداس العيد', 13, len(secs)),
]
groups = []
for en, ar, a, b in RG:
    groups.append(dict(id=f'resg{a}', title=dict(en=en, ar=ar), holy='easter' if a == 0 else None,
                       sections=[dict(id=s['id'], title=s['title'], file='resurrection.json') for s in secs[a:b]]))
books = []
if os.path.exists(f'{D}/pascha/index.json'):
    pidx = json.load(open(f'{D}/pascha/index.json'))
    books.append(dict(id='pascha', title=dict(en='Book of the Holy Pascha', ar='كتاب البصخة المقدسة', cop='Ⲡⲓϫⲱⲙ ⲛ̀ⲧⲉ Ⲡⲓⲡⲁⲥⲭⲁ ⲉⲑⲟⲩⲁⲃ'),
                      source='Book of the Holy Pascha (Virgin Mary and Archangel Michael Coptic Orthodox Church of Connecticut)',
                      groups=pidx['groups']))
books.append(dict(id='resurrection', title=res['title'], source=res['source'], groups=groups))
json.dump(dict(version=1, books=books), open(f'{D}/library.json', 'w'), ensure_ascii=False, indent=1)
print('books', [b['id'] for b in books])
