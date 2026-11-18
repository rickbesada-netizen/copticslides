/* Transliteration engines for the Coptic Reader app.
 *  copticToLatin   – Coptic (Unicode) -> English letters (Greco-Bohairic church pronunciation)
 *  copticToArabic  – Coptic (Unicode) -> Arabic letters
 *  arabicToLatin   – Arabic -> English letters (Franco / Arabizi style, approximate)
 *  latinToArabic   – English -> Arabic letters (approximate phonetic)
 */
(function (root) {
  'use strict';
  const JENKIM = '̀', OVER = '̅';
  const lower = s => s.toLowerCase();

  // ---- Coptic helpers ------------------------------------------------------
  // Normalise capitals to small letters for rule lookups (Coptic capitals are even code points)
  function cLower(ch) {
    const c = ch.codePointAt(0);
    if (c >= 0x2C80 && c <= 0x2CE3 && c % 2 === 0) return String.fromCodePoint(c + 1);
    if (c >= 0x03E2 && c <= 0x03EF && c % 2 === 0) return String.fromCodePoint(c + 1);
    return ch;
  }
  const isUpperCop = ch => cLower(ch) !== ch;
  const FRONT = new Set(['ⲉ', 'ⲏ', 'ⲓ', 'ⲩ']);
  const VOWELS = new Set(['ⲁ', 'ⲉ', 'ⲏ', 'ⲓ', 'ⲟ', 'ⲩ', 'ⲱ']);

  // Nomina sacra (abbreviated holy names with overline)
  const NOMINA = [
    [/Ⲡ̅ϭ̅ⲥ̅|Ⲡϭ̅ⲥ̅|Ⲡ̅ⲟ̅ⲥ̅|Ⲡⲟ̅ⲥ̅/g, 'Ⲡϭⲟⲓⲥ'], [/ⲡ̅ϭ̅ⲥ̅|ⲡϭ̅ⲥ̅|ⲡ̅ⲟ̅ⲥ̅|ⲡⲟ̅ⲥ̅/g, 'ⲡϭⲟⲓⲥ'],
    [/ϭ̅ⲥ̅/g, 'ϭⲟⲓⲥ'],
    [/Ⲓ̅ⲏ̅ⲥ̅|Ⲓⲏ̅ⲥ̅|Ⲓ̅ⲥ̅/g, 'Ⲓⲏⲥⲟⲩⲥ'], [/Ⲡ̅ⲭ̅ⲥ̅|Ⲡⲭ̅ⲥ̅/g, 'Ⲡⲓⲭⲣⲓⲥⲧⲟⲥ'], [/Ⲭ̅ⲥ̅|ⲭ̅ⲥ̅/g, 'Ⲭⲣⲓⲥⲧⲟⲥ'],
    [/Ⲫ̅ϯ̅|Ⲫϯ̅/g, 'Ⲫⲛⲟⲩϯ'], [/ⲫ̅ϯ̅/g, 'ⲫⲛⲟⲩϯ'], [/ⲁ̅ⲗ̅/g, 'ⲁⲗⲗⲏⲗⲟⲩⲓⲁ'], [/Ⲁ̅ⲗ̅/g, 'Ⲁⲗⲗⲏⲗⲟⲩⲓⲁ'],
    [/ⲉ̅ⲑ̅ⲩ̅|ⲉⲑ̅ⲩ̅/g, 'ⲉⲑⲟⲩⲁⲃ'], [/Ⲓ̅ⲗ̅ⲏ̅ⲙ̅|Ⲓⲗ̅ⲏ̅ⲙ̅/g, 'Ⲓⲉⲣⲟⲩⲥⲁⲗⲏⲙ'], [/ⲡ̅ⲛ̅ⲁ̅|ⲡ̅ⲛ̅ⲁ̅/g, 'ⲡⲛⲉⲩⲙⲁ'],
    [/Ⲡ̅ⲛ̅ⲁ̅/g, 'Ⲡⲛⲉⲩⲙⲁ'], [/ⲓ̅ⲥ̅ⲗ̅/g, 'ⲓⲥⲣⲁⲏⲗ']
  ];
  function expandNomina(s) { for (const [re, r] of NOMINA) s = s.replace(re, r); return s; }

  // tokenise a Coptic word into [letter, jenkim:boolean]
  function letters(word) {
    const out = [];
    for (const ch of word) {
      if (ch === JENKIM) { if (out.length) out[out.length - 1].j = true; continue; }
      if (ch === OVER) continue;
      out.push({ c: cLower(ch), up: isUpperCop(ch), raw: ch, j: false });
    }
    return out;
  }
  const isCop = ch => /[Ⲁ-⳿Ϣ-ϯ]/.test(ch);

  const LAT = {
    'ⲁ': 'a', 'ⲃ': 'v', 'ⲅ': 'g', 'ⲇ': 'd', 'ⲉ': 'e', 'ⲋ': 'so', 'ⲍ': 'z', 'ⲏ': 'ee', 'ⲑ': 'th', 'ⲓ': 'i', 'ⲕ': 'k', 'ⲗ': 'l',
    'ⲙ': 'm', 'ⲛ': 'n', 'ⲝ': 'x', 'ⲟ': 'o', 'ⲡ': 'p', 'ⲣ': 'r', 'ⲥ': 's', 'ⲧ': 't', 'ⲩ': 'i', 'ⲫ': 'f', 'ⲭ': 'kh', 'ⲯ': 'ps',
    'ⲱ': 'o', 'ϣ': 'sh', 'ϥ': 'f', 'ϧ': 'kh', 'ϩ': 'h', 'ϫ': 'j', 'ϭ': 'ch', 'ϯ': 'ti'
  };
  const AR = {
    'ⲁ': 'ا', 'ⲃ': 'ف', 'ⲅ': 'ج', 'ⲇ': 'د', 'ⲉ': 'ي', 'ⲋ': 'سو', 'ⲍ': 'ز', 'ⲏ': 'ي', 'ⲑ': 'ث', 'ⲓ': 'ي', 'ⲕ': 'ك', 'ⲗ': 'ل',
    'ⲙ': 'م', 'ⲛ': 'ن', 'ⲝ': 'كس', 'ⲟ': 'و', 'ⲡ': 'ب', 'ⲣ': 'ر', 'ⲥ': 'س', 'ⲧ': 'ت', 'ⲩ': 'ي', 'ⲫ': 'ف', 'ⲭ': 'خ', 'ⲯ': 'بس',
    'ⲱ': 'و', 'ϣ': 'ش', 'ϥ': 'ف', 'ϧ': 'خ', 'ϩ': 'ه', 'ϫ': 'ج', 'ϭ': 'تش', 'ϯ': 'تي'
  };
  const AR_INIT = { 'ⲁ': 'آ', 'ⲉ': 'إ', 'ⲏ': 'إي', 'ⲓ': 'إي', 'ⲟ': 'أو', 'ⲱ': 'أو', 'ⲩ': 'إي' };

  function copWordLatin(word) {
    const L = letters(word);
    let out = '';
    for (let i = 0; i < L.length; i++) {
      const { c, j } = L[i];
      const n = L[i + 1] ? L[i + 1].c : '';
      const p = L[i - 1] ? L[i - 1].c : '';
      let s;
      if (c === 'ⲟ' && n === 'ⲩ') {
        // ⲟⲩ = ou; before a vowel it is 'w'
        const nn = L[i + 2] ? L[i + 2].c : '';
        s = VOWELS.has(nn) && nn !== 'ⲓ' ? 'w' : 'ou'; i++;
        if (j && !out) s = 'o' + s.slice(1);
      } else if (c === 'ⲩ' && (p === 'ⲁ' || p === 'ⲉ')) {
        s = VOWELS.has(n) ? 'v' : 'v';
      } else if (c === 'ⲭ') {
        s = FRONT.has(n) ? 'sh' : 'kh';
      } else if (c === 'ⲅ' && (n === 'ⲅ' || n === 'ⲕ' || n === 'ⲭ')) {
        s = 'n';
      } else if (c === 'ⲅ') {
        s = FRONT.has(n) ? 'g' : 'gh';
      } else if (c === 'ⲃ' && (p === 'ⲃ' || n === 'ⲃ' || p === 'ⲙ')) {
        s = 'b';
      } else if (c === 'ⲏ') {
        s = 'i';
      } else if (c === 'ⲓ' && VOWELS.has(p) && p !== 'ⲓ' && VOWELS.has(n)) {
        s = 'y';
      } else {
        s = LAT[c] || c;
      }
      if (j && !VOWELS.has(c)) s = 'e' + s;
      out += s;
    }
    // capitalise if first Coptic letter was a capital
    if (L.length && L[0].up) out = out.charAt(0).toUpperCase() + out.slice(1);
    return out;
  }

  function copWordArabic(word) {
    const L = letters(word);
    let out = '';
    for (let i = 0; i < L.length; i++) {
      const { c, j } = L[i];
      const n = L[i + 1] ? L[i + 1].c : '';
      const p = L[i - 1] ? L[i - 1].c : '';
      let s;
      const first = out === '';
      if (c === 'ⲟ' && n === 'ⲩ') { s = first ? 'أو' : 'و'; i++; }
      else if (c === 'ⲩ' && (p === 'ⲁ' || p === 'ⲉ')) s = 'ف';
      else if (c === 'ⲭ') s = FRONT.has(n) ? 'ش' : 'خ';
      else if (c === 'ⲅ' && (n === 'ⲅ' || n === 'ⲕ' || n === 'ⲭ')) s = 'ن';
      else if (c === 'ⲃ' && (p === 'ⲃ' || n === 'ⲃ' || p === 'ⲙ')) s = 'ب';
      else if (first && AR_INIT[c]) s = AR_INIT[c];
      else if (c === 'ⲉ' && i === L.length - 1) s = 'ي';
      else if (c === 'ⲉ') s = (p && !VOWELS.has(p)) ? 'ي' : 'ي';
      else if (c === 'ⲁ' && i === L.length - 1) s = 'ا';
      else s = AR[c] || c;
      if (j && !VOWELS.has(c)) s = (first ? 'إ' : 'ي') + s;
      out += s;
    }
    return out;
  }

  function mapWords(text, fn) {
    text = expandNomina(text);
    // split keeping non-Coptic runs
    return text.replace(/[Ⲁ-⳿Ϣ-ϯ̀̅]+/g, w => fn(w))
      .replace(/:/g, ':');
  }
  const copticToLatin = t => mapWords(t, copWordLatin);
  const copticToArabic = t => mapWords(t, copWordArabic).replace(/\./g, '.');

  // ---- Arabic -> Latin (Franco) ---------------------------------------------
  const SUN = new Set('تثدذرزسشصضطظلن'.split(''));
  const A2L = {
    'ا': 'a', 'أ': 'a', 'إ': 'e', 'آ': 'aa', 'ء': "'", 'ؤ': "o'", 'ئ': "e'", 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'g', 'ح': 'h',
    'خ': 'kh', 'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': "'",
    'غ': 'gh', 'ف': 'f', 'ق': 'k', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y', 'ى': 'a', 'ة': 'a',
    'ـ': '', '،': ',', '؛': ';', '؟': '?'
  };
  const LONG_V = { 'ا': 'a', 'و': 'o', 'ي': 'i', 'ى': 'a' };
  const HARAKAT = { 'َ': 'a', 'ُ': 'o', 'ِ': 'e', 'ً': 'an', 'ٌ': 'on', 'ٍ': 'en', 'ْ': '', 'ّ': '' };
  const AR_WORDS = { 'الله': 'Allah', 'يارب': 'ya Rab', 'آمين': 'amen', 'المسيح': 'el-Maseeh', 'يسوع': 'Yasoo\'', 'هلليلويا': 'alleluia', 'ربنا': 'Rabbena', 'لأن': 'le-an', 'لأنه': 'le-annahu', 'الذي': 'allazi', 'الذى': 'allazi', 'التي': 'allati', 'هذا': 'haza', 'كل': 'kol', 'مع': 'ma\'a', 'من': 'men', 'في': 'fi', 'فى': 'fi', 'على': '\'ala', 'علي': '\'ala', 'إلى': 'ela', 'الى': 'ela', 'يا': 'ya', 'أيها': 'ayyoha', 'لنا': 'lana', 'نحن': 'nahno', 'أنت': 'anta', 'هو': 'howa', 'ارحمنا': 'erhamna', 'الرب': 'er-Rab', 'السلام': 'es-salam', 'القيامة': 'el-qeyama', 'قام': 'qam', 'المجد': 'el-magd' };
  function arWordLatin(w) {
    if (AR_WORDS[w]) return AR_WORDS[w];
    const chars = [...w];
    let out = '';
    let i = 0;
    if (w.startsWith('ال') && chars.length > 3) {
      const third = chars[2];
      out = SUN.has(third) ? 'el-' : 'el-';
      i = 2;
    } else if (/^(وال|بال|فال|كال)/.test(w) && chars.length > 4) {
      out = A2L[chars[0]] === 'w' ? 'wel-' : (A2L[chars[0]] + 'el-'); i = 3;
    } else if (/^لل/.test(w) && chars.length > 3) { out = 'lel-'; i = 2; }
    let run = 0; const startedVowel = /[aeiou]-?$/.test(out);
    let hadVowel = false;
    for (; i < chars.length; i++) {
      const c = chars[i];
      const n = chars[i + 1];
      if (HARAKAT[c] !== undefined) { out += HARAKAT[c]; run = 0; continue; }
      if (c === 'ة' && i === chars.length - 1) { out += 'a'; continue; }
      if ((c === 'و' || c === 'ي' || c === 'ا' || c === 'ى') && i > 0 && out && !/[aeiou]$/.test(out)) {
        // long vowel after consonant
        out += c === 'و' ? 'oo' : c === 'ي' ? 'ee' : 'a';
        run = 0; hadVowel = true; continue;
      }
      const m = A2L[c];
      if (m === undefined) { out += c; run = 0; continue; }
      const isV = /^[aeiou]/.test(m);
      if (!isV && m) {
        // Arabic never starts with a cluster and never has 3 consonants in a row
        if ((!hadVowel && run === 1) || run >= 2) { out += 'a'; run = 0; hadVowel = true; }
        run++;
      } else { run = 0; hadVowel = true; }
      out += m;
    }
    out = out.replace(/aaa+/g, 'aa').replace(/^'/, '').replace(/-a/, '-');
    return out;
  }
  function arabicToLatin(t) {
    return t.replace(/[ء-ْـ]+/g, w => arWordLatin(w))
      .replace(/(^|[.!?:\n]\s*)([a-z])/g, (m, a, b) => a + b.toUpperCase());
  }

  // ---- English -> Arabic letters (approximate) -------------------------------
  const E2A_DI = [
    ['tion', 'شن'], ['sion', 'جن'], ['ough', 'و'], ['igh', 'اي'], ['augh', 'و'], ['ee', 'ي'], ['ea', 'ي'], ['oo', 'و'], ['ou', 'او'],
    ['ow', 'او'], ['oa', 'و'], ['ai', 'اي'], ['ay', 'اي'], ['oy', 'وي'], ['oi', 'وي'], ['au', 'و'], ['aw', 'و'], ['ie', 'ي'],
    ['th', 'ث'], ['sh', 'ش'], ['ch', 'تش'], ['ph', 'ف'], ['gh', 'غ'], ['wh', 'و'], ['ck', 'ك'], ['qu', 'كو'], ['ng', 'نج'], ['kn', 'ن'], ['wr', 'ر']
  ];
  const E2A = {
    a: 'ا', b: 'ب', c: 'ك', d: 'د', e: 'ي', f: 'ف', g: 'ج', h: 'ه', i: 'ي', j: 'ج', k: 'ك', l: 'ل', m: 'م', n: 'ن', o: 'و', p: 'ب',
    q: 'ك', r: 'ر', s: 'س', t: 'ت', u: 'ا', v: 'ف', w: 'و', x: 'كس', y: 'ي', z: 'ز'
  };
  const E_WORDS = {
    the: 'ذا', of: 'أوف', and: 'آند', to: 'تو', you: 'يو', your: 'يور', is: 'إز', he: 'هي', his: 'هيز', him: 'هيم', a: 'أ', in: 'إن',
    o: 'أو', lord: 'لورد', god: 'جاد', christ: 'كرايست', jesus: 'جيزس', amen: 'آمين', alleluia: 'هلليلويا', holy: 'هولي',
    spirit: 'سبيريت', father: 'فاذر', son: 'سان', mary: 'ميري', glory: 'جلوري', mercy: 'ميرسي', have: 'هاف', us: 'اس', our: 'أور',
    who: 'هو', are: 'آر', we: 'وي', for: 'فور', all: 'أول', be: 'بي', with: 'ويذ', peace: 'بيس', virgin: 'فيرجن', saint: 'سينت',
    risen: 'ريزن', on: 'أون', not: 'نوت', but: 'بات', from: 'فروم', by: 'باي', us: 'آس', will: 'ويل', may: 'ماي', life: 'لايف', death: 'ديث', dead: 'ديد', light: 'لايت', one: 'وان', heaven: 'هيفن', earth: 'إيرث', name: 'نيم', people: 'بيبل', church: 'تشيرش', love: 'لاف', day: 'داي', say: 'ساي', saying: 'سايينج', said: 'سيد', through: 'ثرو', those: 'ذوز', these: 'ذيز', there: 'ذير', their: 'ذير', they: 'ذاي', them: 'ذيم', what: 'وات', when: 'وين', which: 'ويتش', was: 'واز', were: 'وير', has: 'هاز', had: 'هاد', come: 'كام', came: 'كيم', do: 'دو', no: 'نو', so: 'سو', as: 'آز', at: 'آت', it: 'إت', an: 'آن', or: 'أور', now: 'ناو', ever: 'إيفر', forever: 'فوريفر', ages: 'إيجيز', give: 'جيف', blessed: 'بليسد', bless: 'بليس', praise: 'بريز', worship: 'ويرشيب', save: 'سيف', grace: 'جريس', angels: 'اينجلز', saints: 'سينتس', resurrection: 'ريزوريكشن', world: 'ويرلد', king: 'كينج', this: 'ذيس', that: 'ذات', my: 'ماي', me: 'مي', i: 'آي'
  };
  function enWordArabic(w) {
    const lw = w.toLowerCase();
    if (E_WORDS[lw]) return E_WORDS[lw];
    let s = lw;
    if (s.length > 3 && s.endsWith('e') && !/[aeiou]e$/.test(s)) s = s.slice(0, -1);
    let out = '';
    for (let i = 0; i < s.length;) {
      let hit = false;
      for (const [k, v] of E2A_DI) {
        if (s.startsWith(k, i)) { out += v; i += k.length; hit = true; break; }
      }
      if (hit) continue;
      const ch = s[i];
      const n = s[i + 1] || '';
      if (ch === 'c' && /[eiy]/.test(n)) out += 'س';
      else if (ch === 'g' && /[eiy]/.test(n)) out += 'ج';
      else if (ch === 'e' && i === 0) out += 'إ';
      else if ((ch === 'a' || ch === 'o' || ch === 'u') && i === 0) out += ch === 'u' ? 'أ' : 'أ';
      else if (ch === 'i' && i === 0) out += 'إ';
      else if (ch === 'e' && i > 0 && i < s.length - 1 && !/[aeiou]/.test(s[i - 1]) && !/[aeiou]/.test(n)) out += '';
      else if (ch === 'e' && i === s.length - 1) out += '';
      else if (ch === 'y' && i === s.length - 1) out += 'ي';
      else if (s[i - 1] === ch) out += '';
      else out += E2A[ch] !== undefined ? E2A[ch] : ch;
      i++;
    }
    return out || w;
  }
  function latinToArabic(t) {
    return t.replace(/[A-Za-z]+/g, w => enWordArabic(w)).replace(/,/g, '،').replace(/\?/g, '؟').replace(/;/g, '؛');
  }

  root.Translit = { copticToLatin, copticToArabic, arabicToLatin, latinToArabic };
  if (typeof module !== 'undefined') module.exports = root.Translit;
})(typeof window !== 'undefined' ? window : globalThis);
