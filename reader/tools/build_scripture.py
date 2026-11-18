import json, re
D = '/home/claude/app/data'
lib = json.load(open(f'{D}/library.json'))
BOOKS = ['Genesis','Exodus','Leviticus','Numbers','Deuteronomy','Joshua','Judges','Ruth','1 Samuel','2 Samuel','1 Kings','2 Kings','1 Chronicles','2 Chronicles',
 'Ezra','Nehemiah','Tobit','Judith','Esther','Job','Psalms','Psalm','Proverbs','Ecclesiastes','Song of Songs','Wisdom','Sirach','Isaiah','Jeremiah','Lamentations','Baruch','Ezekiel','Daniel',
 'Hosea','Joel','Amos','Obadiah','Jonah','Micah','Nahum','Habakkuk','Zephaniah','Haggai','Zechariah','Malachi','Matthew','Mark','Luke','John','Acts',
 'Romans','1 Corinthians','2 Corinthians','Galatians','Ephesians','Philippians','Colossians','1 Thessalonians','2 Thessalonians','1 Timothy','2 Timothy',
 'Titus','Philemon','Hebrews','James','1 Peter','2 Peter','1 John','2 John','3 John','Jude','Revelation']
order = {b: i for i, b in enumerate(BOOKS)}
pat = re.compile(r'\b(' + '|'.join(re.escape(b) for b in sorted(BOOKS, key=len, reverse=True)) + r')\s*\[?\s*(\d{1,3})\s*:\s*(\d{1,3}(?:\s*[-–—,]\s*\d{1,3}(?::\d{1,3})?)*)\]?')
files = {}
for did, m in lib['docs'].items():
    files.setdefault(m['file'], []).append(did)
out = []
seen = set()
for f, dids in files.items():
    d = json.load(open(f'{D}/{f}'))
    for s in d['sections']:
        if s['id'] not in dids: continue
        for i, r in enumerate(s['rows']):
            t = r.get('en') or ''
            for m in pat.finditer(t[:160]):
                book = 'Psalms' if m.group(1) == 'Psalm' else m.group(1)
                ref = f"{book} {m.group(2)}:{re.sub(r'\s+', '', m.group(3))}"
                key = (ref, s['id'])
                if key in seen: continue
                seen.add(key)
                out.append(dict(ref=ref, book=book, ch=int(m.group(2)), doc=s['id'], row=i, title=s['title']))
out.sort(key=lambda e: (order.get(e['book'], 99), e['ch'], e['ref']))
json.dump(out, open(f'{D}/scripture.json', 'w'), ensure_ascii=False)
print(len(out), out[:3])
