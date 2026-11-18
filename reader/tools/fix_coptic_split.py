import json, re, collections, unicodedata, sys
F = '/home/claude/app/data/resurrection.json'
b = json.load(open(F))
def key(w):
    w = unicodedata.normalize('NFD', w)
    w = re.sub('[̀̅]', '', w)
    return ''.join(chr(ord(c) + 1) if (0x2C80 <= ord(c) <= 0x2CE3 or 0x03E2 <= ord(c) <= 0x03EF) and ord(c) % 2 == 0 else c for c in w)
cnt = collections.Counter()
for s in b['sections']:
    for r in s['rows']:
        for w in re.findall(r'[Ⲁ-⳿Ϣ-ϯ̀̅]+', r.get('cop', '')):
            cnt[key(w)] += 1
extra = {}
try:
    extra = json.load(open('/home/claude/work/coptic_text.json'))
except Exception:
    pass
for t in extra.values():
    for w in re.findall(r'[Ⲁ-⳿Ϣ-ϯ̀̅]+', t):
        cnt[key(w)] += 1
fixes = 0
def fix(text):
    global fixes
    toks = text.split(' ')
    out = []
    for tok in toks:
        if len(out) >= 2:
            a2, a1 = out[-2], out[-1]
            parts = [key(re.sub(r'[^\u2c80-\u2cff\u03e2-\u03ef\u0300\u0305]', '', x)) for x in (a2, a1, tok)]
            if all(parts) and re.fullmatch(r'[\u2c80-\u2cff\u03e2-\u03ef\u0300\u0305]+', a2 + a1) and cnt[''.join(parts)] >= 1 and min(cnt[q] for q in parts) < 2:
                out[-2:] = [a2 + a1 + tok]; fixes += 1; continue
        if out:
            a = out[-1]
            ka, kb = key(re.sub(r'[^Ⲁ-⳿Ϣ-ϯ̀̅]', '', a)), key(re.sub(r'[^Ⲁ-⳿Ϣ-ϯ̀̅]', '', tok))
            if ka and kb and re.fullmatch(r'[Ⲁ-⳿Ϣ-ϯ̀̅]+', a) and re.match(r'[Ⲁ-⳿Ϣ-ϯ]', tok):
                kj = ka + kb
                if cnt[kj] >= 2 and (cnt[ka] < 2 or cnt[kb] < 2) and cnt[kj] >= min(cnt[ka], cnt[kb]):
                    out[-1] = a + tok; fixes += 1; continue
        out.append(tok)
    return ' '.join(out)
for s in b['sections']:
    for r in s['rows']:
        if r.get('cop'):
            r['cop'] = '\n'.join(fix(l) for l in r['cop'].split('\n'))
json.dump(b, open(F, 'w'), ensure_ascii=False)
print('joined', fixes)
