import json, re
raw = json.load(open('/home/claude/work/agpeya_raw.json'))
T = {
 'Introductory Prayer': ('Introductory Prayer', 'مقدمة كل ساعة', 'intro'),
 'The Prayer of the First Hour': ('First Hour (Prime)', 'صلاة باكر', 'prime'),
 'The Prayer of the Third Hour': ('Third Hour (Terce)', 'صلاة الساعة الثالثة', 'terce'),
 'The Prayer of the Sixth Hour': ('Sixth Hour (Sext)', 'صلاة الساعة السادسة', 'sext'),
 'The Prayer of the Ninth Hour': ('Ninth Hour (None)', 'صلاة الساعة التاسعة', 'none'),
 'The Prayer of the Eleventh Hour': ('Eleventh Hour (Vespers)', 'صلاة الغروب', 'vespers'),
 'The Prayer of the Twelfth Hour': ('Twelfth Hour (Compline)', 'صلاة النوم', 'compline'),
 'The Prayer of the Veil': ('Prayer of the Veil', 'صلاة الستار', 'veil'),
 'Midnight Prayer': ('Midnight Prayer', 'صلاة نصف الليل', 'midnight'),
 'The Priests’ Absolution': ('Priests’ Absolution', 'تحليل الكهنة', 'absolution'),
 'Selected Prayers': ('Selected Prayers', 'صلوات مختارة', 'selected'),
 'Psalms Index': ('Psalms Index', 'فهرس المزامير', 'psindex'),
}
secs = []
for d in raw:
    en, ar, sid = T.get(d['header'], (d['header'], d['header'], re.sub(r'\W+', '-', d['header'].lower())))
    rows = []
    for r in d['rows']:
        t = r['en'].strip()
        if len(t) <= 2 or t.upper().startswith('THIS PAGE NOT TO BE USED') or t == d['header']:
            continue
        if r.get('kind') == 'heading':
            t = t.title() if t.isupper() else t
            t = re.sub(r'\bOf\b', 'of', re.sub(r'\bThe\b(?!^)', 'the', t)); t = t[0].upper() + t[1:]
            r['en'] = t
        rows.append(r)
    secs.append(dict(id='ag-' + sid, title=dict(en=en, ar=ar), rows=rows))
json.dump(dict(source='Agpia, The Prayer Book of the Seven Canonical Hours (C.O.P.T., Sydney, 2000; NKJV)', sections=secs),
          open('/home/claude/app/data/agpeya.json', 'w'), ensure_ascii=False)
print([(s['id'], len(s['rows'])) for s in secs])
