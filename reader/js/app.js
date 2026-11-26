/* Liturgy Reader – main application */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const el = (tag, attrs = {}, ...kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === undefined || v === null || v === false) continue;
      if (k === 'class') e.className = v; else if (k === 'html') e.innerHTML = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v);
    }
    for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) e.append(k.nodeType ? k : document.createTextNode(k));
    return e;
  };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ------------------------------------------------------------------ settings
  const ALL_COLS = ['en', 'cop', 'ar', 'cop_lat', 'cop_ar', 'ar_lat', 'en_ar'];
  const RTL_COLS = new Set(['ar', 'cop_ar', 'en_ar']);
  const ROLES = ['PRIEST', 'DEACON', 'PEOPLE', 'READER', 'ALL', 'BISHOP'];
  const DEFAULTS = {
    ui: (navigator.language || 'en').slice(0, 2) === 'ar' ? 'ar' : 'en', theme: 'book', mode: 'scroll', fs: 20, layout: 'auto',
    order: ALL_COLS.slice(), on: { en: true, cop: true, ar: true }, roles: { PRIEST: true, DEACON: true, PEOPLE: true, READER: true, ALL: true, BISHOP: true },
    comments: true, bookPhon: true, copScan: true, slides: true, dayStart: 0, fixedJdn: null
  };
  let S;
  function loadSettings() {
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem('lr.settings') || '{}'); } catch (e) { /* storage unavailable */ }
    S = Object.assign(JSON.parse(JSON.stringify(DEFAULTS)), saved);
    if (!Array.isArray(S.order) || S.order.length !== ALL_COLS.length) S.order = ALL_COLS.slice();
    S.roles = Object.assign({}, DEFAULTS.roles, S.roles);
    if (!['book', 'night', 'light', 'sepia'].includes(S.theme)) S.theme = 'book';
  }
  function save() { try { localStorage.setItem('lr.settings', JSON.stringify(S)); } catch (e) { /* ignore */ } }
  const t = k => { const L = I18N[S.ui] || I18N.en; return (k in L) ? L[k] : (k in I18N.en ? I18N.en[k] : k); };
  const tt = o => !o ? '' : (S.ui === 'ar' ? (o.ar || o.en) : (o.en || o.ar));
  const locale = () => S.ui === 'ar' ? 'ar-EG' : S.ui;

  function applyTheme() {
    const r = document.documentElement;
    r.dataset.theme = S.theme;
    r.style.setProperty('--fs', S.fs + 'px');
    r.lang = S.ui; r.dir = S.ui === 'ar' ? 'rtl' : 'ltr';
    document.body.classList.toggle('hide-comments', !S.comments);
    document.title = t('app');
  }

  // ------------------------------------------------------------------ dates
  function nowJDN() {
    if (S.fixedJdn) return S.fixedJdn;
    const d = new Date();
    let j = CopticCal.todayJDN(d);
    if (S.dayStart && d.getHours() >= S.dayStart) j += 1;
    return j;
  }
  const gregText = j => { const g = CopticCal.jdnToGreg(j); return new Date(g.y, g.m - 1, g.d).toLocaleDateString(locale(), { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }); };
  const copText = j => CopticCal.formatCoptic(j, S.ui === 'ar' ? 'ar' : 'en');

  // ------------------------------------------------------------------ data
  let LIB = null;
  const cache = new Map();
  const getJSON = url => { if (!cache.has(url)) cache.set(url, fetch(url).then(r => { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); })); return cache.get(url); };
  async function library() { if (!LIB) { LIB = await getJSON('data/library.json'); addReadingNodes(LIB); } return LIB; }
  async function loadDoc(id) {
    const lib = await library();
    const m = lib.docs[id];
    if (!m) return null;
    if (m.virtual) return { meta: m, sec: await buildReadingDoc(id) };
    const d = await getJSON('data/' + m.file);
    const sec = d.sections.find(s => s.id === (m.parent || id));
    if (!sec) return null;
    if (!m.parent) return { meta: m, sec };
    return { meta: m, sec: { id, title: m.title, rows: sec.rows.slice(m.start, m.end == null ? undefined : m.end) } };
  }
  const nodeDocs = n => (n ? n.items.filter(x => x.doc).map(x => x.doc) : []);
  function nodeOfDoc(id) {
    let last = null;
    try { last = sessionStorage.getItem('lr.node'); } catch (e) { /* ignore */ }
    if (last && LIB.nodes[last] && nodeDocs(LIB.nodes[last]).includes(id)) return LIB.nodes[last];
    return Object.values(LIB.nodes).find(n => nodeDocs(n).includes(id)) || null;
  }
  function parentOfNode(nid) {
    return Object.values(LIB.nodes).find(n => n.items.some(x => x.node === nid)) || null;
  }
  const iconOf = key => (window.TILE_ART[key] || window.TILE_ART.default);


  // ------------------------------------------------------------------ daily readings (Katameros)
  // Readings > Vespers / Matins / Liturgy, built for the selected date from the Katameros references
  // (data/katameros.json), the Synaxarium (data/synaxarium.json) and the deacon's responses.
  const RD = {
    'rd-v-pg': { node: 'rd-vespers', svc: 'vespers', part: 'pg', title: { en: 'Psalm and Gospel', ar: 'المزمور والإنجيل' } },
    'rd-m-pg': { node: 'rd-matins', svc: 'matins', part: 'pg', title: { en: 'Psalm and Gospel', ar: 'المزمور والإنجيل' } },
    'rd-l-pauline': { node: 'rd-liturgy', svc: 'liturgy', part: 'pauline', title: { en: 'Pauline Epistle', ar: 'البولس' } },
    'rd-l-catholic': { node: 'rd-liturgy', svc: 'liturgy', part: 'catholic', title: { en: 'Catholic Epistle', ar: 'الكاثوليكون' } },
    'rd-l-acts': { node: 'rd-liturgy', svc: 'liturgy', part: 'acts', title: { en: 'Praxis', ar: 'الإبركسيس' } },
    'rd-l-synax': { node: 'rd-liturgy', svc: 'liturgy', part: 'synax', title: { en: 'Synaxarion', ar: 'السنكسار' } },
    'rd-l-pg': { node: 'rd-liturgy', svc: 'liturgy', part: 'pg', title: { en: 'Psalm and Gospel', ar: 'المزمور والإنجيل' } },
  };
  function addReadingNodes(lib) {
    if (lib.nodes['rd-liturgy']) return;
    for (const [id, d] of Object.entries(RD)) lib.docs[id] = { virtual: true, title: d.title, heads: [] };
    const node = (id, en, ar, icon, docs) => (lib.nodes[id] = { id, title: { en, ar }, icon, view: 'list', items: docs.map(doc => ({ doc })) });
    node('rd-vespers', 'Vespers', 'عشية', 'vespers', ['rd-v-pg']);
    node('rd-matins', 'Matins', 'باكر', 'matins', ['rd-m-pg']);
    node('rd-liturgy', 'Liturgy', 'القداس', 'liturgy', ['rd-l-pauline', 'rd-l-catholic', 'rd-l-acts', 'rd-l-synax', 'rd-l-pg']);
    const r = lib.nodes.readings;
    if (r) r.items = [{ node: 'rd-vespers' }, { node: 'rd-matins' }, { node: 'rd-liturgy' }, ...r.items.filter(x => x.special !== 'occasion-readings'), { special: 'occasion-readings', title: { en: "Today's Readings", ar: 'قراءات اليوم' }, icon: 'today' }];
  }

  const AR_BOOK = { Psalm: 'المزامير', Matthew: 'متى', Mark: 'مرقس', Luke: 'لوقا', John: 'يوحنا', Acts: 'أعمال الرسل', Romans: 'رومية',
    '1 Corinthians': 'كورنثوس الأولى', '2 Corinthians': 'كورنثوس الثانية', Galatians: 'غلاطية', Ephesians: 'أفسس', Philippians: 'فيلبي',
    Colossians: 'كولوسي', '1 Thessalonians': 'تسالونيكي الأولى', '2 Thessalonians': 'تسالونيكي الثانية', '1 Timothy': 'تيموثاوس الأولى',
    '2 Timothy': 'تيموثاوس الثانية', Titus: 'تيطس', Philemon: 'فليمون', Hebrews: 'العبرانيين', James: 'يعقوب', '1 Peter': 'بطرس الأولى',
    '2 Peter': 'بطرس الثانية', '1 John': 'يوحنا الأولى', '2 John': 'يوحنا الثانية', '3 John': 'يوحنا الثالثة', Jude: 'يهوذا', Revelation: 'رؤيا يوحنا' };
  const arNum = s => s.replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]).replace(/&/g, 'و');
  // "13:24-43" or "1:1-14 & 2:1-4" or "104:4,3" -> tappable parts, each a plain reference
  const refParts = r => r.ref.split(/\s*[&;]\s*/).reduce((acc, part) => {
    const c = /^(\d+):/.exec(part);
    if (c) acc.push(r.book + ' ' + part); else if (acc.length) acc.push(acc[acc.length - 1].replace(/:.*$/, ':') + part); return acc;
  }, []);
  const FEAST_DAYS = new Set(['1-1', '1-17', '4-28', '4-29', '5-6', '5-10', '5-11', '5-12', '5-13', '6-8', '7-29', '9-24', '12-13']);

  // which Katameros entry applies on day j
  async function readingsFor(j) {
    const K = await getJSON('data/katameros.json');
    const c = CopticCal.jdnToCoptic(j), key = c.m + '-' + c.d;
    const E = CopticCal.easterJDN(CopticCal.jdnToGreg(j).y), diff = j - E;
    const sunday = (j + 1) % 7 === 0;
    const day = Object.assign({ src: 'Katameros, Days of the Year, p. ' + K.days[key]?.page }, K.days[key]);
    if (diff >= -6 && diff <= -1) return { pascha: true, day };                        // Holy Week: Pascha book
    if (diff === 0) return Object.assign({ src: 'Katameros of the Sundays, Easter' }, K.sundays.easter);
    if (sunday && !FEAST_DAYS.has(key)) {
      let k = null;
      if (diff >= -56 && diff <= -14 && diff % 7 === 0) k = 'lent-' + (8 + diff / 7);   // E-56 pre-Lent ... E-14 sixth Sunday
      else if (diff >= 7 && diff <= 35) k = 'pent-' + diff / 7;
      else if (diff === 42) k = 'pent-6';
      else if (diff === 49) k = 'pentecost';
      else if (c.m === 13) k = '13-1';
      else { const n = Math.ceil(c.d / 7); k = n >= 5 ? 'fifth' : c.m + '-' + n; }
      const e = K.sundays[k];
      if (e) return Object.assign({ src: 'Katameros of the Sundays, ' + e.occasion + ', p. ' + e.page }, e);
    }
    if (diff === 39) return Object.assign({ src: 'Katameros of the Sundays, Ascension' }, K.sundays.ascension);
    if ((diff > -56 && diff < -7) || (diff > 0 && diff < 49)) return { missing: diff < 0 ? 'lent' : 'fifty', day };
    return day;
  }

  // the deacon's responses around each reading, cut from the Deacon book by heading
  async function deaconSlice(secId, fromHead, toHead) {
    const d = await getJSON('data/deacon.json');
    const rows = d.sections.find(s => s.id === secId).rows;
    const find = (h, from = 0) => rows.findIndex((r, i) => i >= from && r.kind === 'heading' && (r.en || '').trim().toUpperCase().startsWith(h.toUpperCase()));
    const a = find(fromHead), b = toHead ? find(toHead, a + 1) : rows.length;
    return rows.slice(a, b < 0 ? undefined : b).map(r => Object.assign({}, r));
  }
  function readingRows(label, r) {
    if (!r) return [{ kind: 'rubric', en: label + ': not listed in the Katameros for this day.' }];
    const parts = refParts(r);
    return [
      { kind: 'heading', en: r.book + ' ' + r.ref, ar: (AR_BOOK[r.book] || r.book) + ' ' + arNum(r.ref) },
      { en: parts.join('; '), cls: 'bgref' },
      { kind: 'rubric', en: 'The scripture passage is displayed below its reference when embedding is permitted by the Bible provider.' },
    ];
  }
  // Announcements are placed around the daily passage; the original
  // deacon-book responses remain in their existing order.
  function readingAnnouncement(part, passage) {
    if (!passage) return [];
    const book = passage.book || '';
    const announcements = {
      pauline: 'A reading from the Epistle of our teacher Saint Paul the Apostle to the ' + (book === 'Hebrews' ? 'Hebrews' : book.replace(/^([12]) /, '$1 ')) + '. May his blessings be with us all. Amen.',
      catholic: 'A reading from the Catholic Epistle of ' + book + '. May his blessings be with us all. Amen.',
      acts: 'A reading from the Acts of our fathers the pure Apostles. May their holy blessings be with us all. Amen.',
      gospel: 'Stand up in the fear of God and listen to the Holy Gospel according to Saint ' + book + '. May his blessings be with us all. Amen.'
    };
    const conclusions = {
      pauline: 'The grace of God the Father be with you all. Amen.',
      catholic: 'Do not love the world or the things in the world. The world is passing away, and its desire; but he who does the will of God abides forever. Amen.',
      acts: 'The word of the Lord shall grow, multiply, be mighty, and be confirmed in the holy Church of God. Amen.',
      gospel: 'Glory be to God forever. Amen.'
    };
    return [
      { kind: 'heading', en: 'Announcement before the reading' },
      { kind: 'rubric', en: announcements[part] || ('A reading from ' + book + '.') },
    ];
  }
  function readingConclusion(part) {
    const texts = {
      pauline: 'The grace of God the Father be with you all. Amen.',
      catholic: 'Do not love the world or the things in the world. The world is passing away, and its desire; but he who does the will of God abides forever. Amen.',
      acts: 'The word of the Lord shall grow, multiply, be mighty, and be confirmed in the holy Church of God. Amen.',
      gospel: 'Glory be to God forever. Amen.'
    };
    return texts[part] ? [{ kind: 'heading', en: 'Conclusion of the reading' }, { kind: 'rubric', en: texts[part] }] : [];
  }
  async function buildReadingDoc(id) {
    const def = RD[id], j = nowJDN();
    const c = CopticCal.jdnToCoptic(j);
    const R = await readingsFor(j);
    const dateLine = copText(j) + ' · ' + gregText(j);
    const head = [{ kind: 'heading', en: tt(def.title) + ' — ' + dateLine, ar: def.title.ar },
      { kind: 'rubric', en: (R.occasion || R.day?.occasion || '') + (R.src ? ' (' + R.src + ')' : '') }];
    let rows = [];
    if (R.pascha) rows = [{ kind: 'rubric', en: 'During Holy Week the readings of each hour are in the Holy Pascha book (Readings › Holy Pascha).' }];
    else if (R.missing && def.part !== 'synax') rows = [{ kind: 'rubric', en: (R.missing === 'lent' ? 'Great Lent weekday' : 'Holy Fifty Days weekday') + ' readings come from the ' + (R.missing === 'lent' ? 'Katameros of Great Lent' : 'Katameros of the Holy Fifty Days') + ', which is not in the library yet.' }];
    else if (def.part === 'synax') {
      const S2 = await getJSON('data/synaxarium.json');
      const e = S2.days[c.m + '-' + c.d];
      rows = await deaconSlice('dc-liturgy-of-st-basil', 'APEKRAN', 'THE TRISAGION');
      const body = e ? [{ kind: 'heading', en: 'Synaxarium — ' + copText(j), ar: 'السنكسار' },
        ...e.titles.map(x => ({ kind: 'rubric', en: x })), ...e.paras.map(x => ({ en: x }))]
        : [{ kind: 'rubric', en: 'This day is not in the Synaxarium book.' }];
      rows = [...body, ...rows];
    } else if (def.svc !== 'liturgy') {
      const svc = R[def.svc] || {};
      rows = await deaconSlice('dc-offering-of-incense-vespers-matins', 'LITANY OF THE GOSPEL', '(Concluding Prayer');
      rows = rows.flatMap(r => /^\(The Psalm\)/.test(r.en || '') ? readingRows('Psalm', svc.psalm) : /^\(The Gospel\)/.test(r.en || '') ? readingRows('Gospel', svc.gospel) : [r]);
      if (!R[def.svc] || (!svc.psalm && !svc.gospel)) rows = [{ kind: 'rubric', en: 'The Katameros has no ' + def.svc + ' reading for this day.' }];
    } else {
      const L = R.liturgy || {};
      const cut = { pauline: ['THE PAULINE EPISTLE', 'THE CATHOLIC EPISTLE', 'Response'], catholic: ['THE CATHOLIC EPISTLE', 'THE ACTS', 'Catholic Epistle Response'],
        acts: ['THE ACTS', 'APEKRAN', 'Response'], pg: ['THE TRISAGION', '- THE THREE MAJOR LITANIES', null] }[def.part];
      rows = (await deaconSlice('dc-liturgy-of-st-basil', cut[0], cut[1])).filter(r => !/^\+\s*The Acts & Sinaxarium/i.test(r.en || ''));
      if (def.part === 'pg') rows = rows.flatMap(r => /^\(The Psalm\)/.test(r.en || '') ? readingRows('Psalm', L.psalm) : /^\(The Gospel\)/.test(r.en || '') ? readingRows('Gospel', L.gospel) : [r]);
      else {
        const label = def.title.en, passage = L[def.part];
        if (def.part === 'pauline') {
          // The deacon book contains a conditional hierarchal introduction
          // and an APETJEEK hymn block. Keep both before the actual reading.
          const bishopStart = rows.findIndex(r => r.kind === 'heading' && /^Introduction in the presence of the Pope/i.test(r.en || ''));
          const hymnStart = rows.findIndex(r => r.kind === 'heading' && /^APETJEEK/i.test(r.en || ''));
          const responseStart = rows.findIndex(r => r.kind === 'heading' && /^Response\s*:/i.test(r.en || ''));
          const intro = rows.slice(0, responseStart < 0 ? rows.length : responseStart);
          const response = responseStart < 0 ? [] : rows.slice(responseStart, bishopStart < 0 ? rows.length : bishopStart);
          const bishop = bishopStart < 0 ? [] : rows.slice(bishopStart, hymnStart < 0 ? rows.length : hymnStart);
          const hymns = hymnStart < 0 ? [] : rows.slice(hymnStart);
          const showBishop = new URLSearchParams(location.search).get('bishop') === '1';
          rows = [...intro,
            ...(showBishop ? bishop : []),
            ...hymns,
            ...readingAnnouncement(def.part, passage),
            ...readingRows(label, passage),
            ...(passage ? readingConclusion(def.part) : []),
            ...response];
        } else if (def.part === 'catholic') {
          // The source explicitly marks where the Catholic Epistle is read.
          const at = rows.findIndex(r => /The Catholic Epistle is now read/i.test(r.en || ''));
          const ins = [...readingAnnouncement(def.part, passage), ...readingRows(label, passage), ...(passage ? readingConclusion(def.part) : [])];
          rows.splice(at < 0 ? rows.length : at, at < 0 ? 0 : 1, ...ins);
        } else {
          const at = rows.findIndex(r => r.kind === 'heading' && /^Response\s*:/i.test(r.en || ''));
          const ins = [...readingAnnouncement(def.part, passage), ...readingRows(label, passage), ...(passage ? readingConclusion(def.part) : [])];
          rows.splice(at < 0 ? rows.length : at, 0, ...ins);
        }
      }
    }
    return { id, title: { en: tt(def.title), ar: def.title.ar }, rows: [...head, ...rows] };
  }

  // ------------------------------------------------------------------ columns
  function colText(row, c) {
    const T = window.Translit;
    switch (c) {
      case 'en': return row.en || '';
      case 'ar': return row.ar || '';
      case 'cop': return row.cop || '';
      case 'cop_lat':
        if (S.bookPhon && row.cop_lat) return row.cop_lat;
        if (S.bookPhon && row.en_ph && (row.cop || row.cop_img)) return row.en_ph;
        return row.cop ? T.copticToLatin(row.cop) : (row.cop_lat || '');
      case 'cop_ar':
        if (S.bookPhon && row.ar_ph) return row.ar_ph;
        return row.cop ? T.copticToArabic(row.cop) : '';
      case 'ar_lat':
        if (row.ar_lat) return row.ar_lat;
        if (S.bookPhon && row.en_ph && !row.cop && !row.cop_img) return row.en_ph;
        return row.ar ? T.arabicToLatin(row.ar) : '';
      case 'en_ar': return row.en ? T.latinToArabic(row.en) : '';
    }
    return '';
  }
  const hasCol = (r, c) => (c === 'cop' && r.cop_img && r.cop_img.length) || !!colText(r, c);
  function activeCols(rows) {
    const on = S.order.filter(c => S.on[c]);
    const cols = on.filter(c => rows.some(r => r.kind !== 'role' && hasCol(r, c)));
    return cols.length ? cols : ['en'];
  }
  function roleLabel(role, c) {
    if (c === 'cop') return I18N.cop_roles[role] || '';
    if (RTL_COLS.has(c)) return (I18N.ar['role_' + role] || '') + ':';
    return (I18N.en['role_' + role] || role) + ':';
  }
  function cellFor(row, c) {
    const d = el('div', { class: 'cell ' + c, 'data-label': t('col_' + c), dir: RTL_COLS.has(c) ? 'rtl' : null });
    if (row.kind === 'role') { d.textContent = roleLabel(row.role, c); return d; }
    if (c === 'cop' && row.cop_img && row.cop_img.length && (S.copScan || !row.cop)) {
      for (const src of row.cop_img) d.append(el('img', { class: 'copimg', src, alt: 'Coptic text', loading: 'lazy' }));
      return d;
    }
    d.textContent = colText(row, c);
    return d;
  }
  const gridTemplate = cols => cols.map(c => (c === 'cop' ? '1.05fr' : '1fr')).join(' ');
  function useStack(cols) {
    if (S.layout === 'stack') return true;
    if (S.layout === 'side') return false;
    const w = window.innerWidth;
    return (w < 560 && cols.length > 1) || (w < 900 && cols.length > 3);
  }
  // attach the current role to every row, and decide visibility
  function prepareRows(rows) {
    let role = null;
    return rows.map((r, i) => {
      if (r.kind === 'role') role = r.role;
      else if (r.kind === 'heading') role = null;
      return Object.assign({ _i: i, _role: r.kind === 'role' ? r.role : role }, r);
    });
  }
  const roleVisible = r => !r._role || S.roles[r._role] !== false;

  // ------------------------------------------------------------------ chrome
  const view = $('#view');
  let current = { id: null, rows: [], cols: [] };
  function setBar(text, o = {}) {
    document.body.classList.toggle('nav', !o.doc && !o.keep);
    $('#barText').textContent = text;
    $('#btnBack').hidden = !o.back;
    $('#btnToc').hidden = !o.doc;
    $('#btnBookmark').hidden = !o.doc;
    $('#btnPresent').hidden = !o.doc;
  }
  function tileIcon(id) { const s = el('span', { class: 'sq t-' + id, html: (window.TILE_ICONS[id] || '') }); return s; }

  // ------------------------------------------------------------------ browsing pages (Coptic Reader style)
  function masthead(small) {
    return el('section', { class: 'masthead' + (small ? ' small' : '') }, el('div', { class: 'emb', html: TILE_ICONS.emblem }),
      el('h1', {}, t('app')), el('p', {}, t('subtitle')),
      el('button', { class: 'ib gear', 'aria-label': t('settings'), onclick: () => { renderSettings(); openDrawer('settings'); }, html: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/></svg>' }));
  }
  function navPanel(title, back, ...content) {
    return el('section', { class: 'navpanel' },
      el('div', { class: 'navhead' },
        back ? el('button', { class: 'ib', 'aria-label': t('back'), onclick: () => go(back), html: '<svg viewBox="0 0 24 24"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>' }) : null,
        el('h2', {}, title),
        el('button', { class: 'ib', 'aria-label': t('bookmarks'), onclick: openBookmarks, html: '<svg viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4-6 4z"/></svg>' }),
        el('button', { class: 'ib', 'aria-label': t('search'), onclick: () => go('#/search/'), html: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/></svg>' })),
      ...content);
  }
  function navPage(...kids) { document.body.classList.add('nav'); view.replaceChildren(...kids); window.scrollTo(0, 0); }
  function itemInfo(it) {
    if (it.node) { const n = LIB.nodes[it.node]; return { href: '#/n/' + n.id, title: n.title, icon: n.icon, holy: n.holy }; }
    if (it.special) return { href: '#/' + it.special, title: it.title, icon: it.icon };
    const m = LIB.docs[it.doc]; return { href: '#/doc/' + it.doc, title: m.title, icon: null };
  }
  function tileFor(info, fallbackIcon) {
    return el('a', { class: 'tile', href: info.href, style: 'text-decoration:none' },
      el('span', { class: 'sq art', html: iconOf(info.icon || fallbackIcon) }), el('span', { class: 'nm' }, tt(info.title)));
  }

  async function viewHome() {
    setBar('', {});
    const lib = await library();
    const j = nowJDN();
    const se = CopticCal.seasonInfo(j);
    const holy = CopticCal.season(j).holy;
    const card = el('div', { class: 'season', onclick: () => go('#/date'), role: 'button', tabindex: 0 },
      el('div', { class: 'ico', html: iconOf(holy === 'easter' ? 'resurrection' : holy ? 'pascha' : (se.key === 'lent' ? 'cross' : 'feast')), style: 'padding:0;overflow:hidden' }),
      el('div', { class: 'txt' },
        el('div', { class: 'lbl' }, t('churchSeason')),
        el('div', { class: 'nm' }, S.ui === 'ar' ? se.ar : se.en),
        S.ui !== 'ar' ? el('div', { class: 'ar', dir: 'rtl' }, se.ar) : null,
        el('div', { class: 'cd' }, '(' + copText(j) + ')'),
        el('div', { class: 'gd' }, gregText(j)),
        S.fixedJdn ? el('div', { class: 'gd', style: 'font-size:13px;opacity:.85' }, '⟲ ' + t('selectDate')) : null,
        todayButtons(holy)));
    const tiles = el('div', { class: 'tiles' }, lib.home.map(it => {
      if (it.special) return tileFor({ href: '#/' + it.special, title: { en: t('cat_' + it.special), ar: it.title.ar }, icon: it.icon });
      const n = lib.nodes[it.node];
      return tileFor({ href: '#/n/' + n.id, title: { en: t('cat_' + n.id), ar: n.title.ar }, icon: n.icon });
    }));
    const guide = el('details',{class:'libpanel',style:'margin-top:12px;padding:16px'},el('summary',{style:'cursor:pointer;font-weight:bold'},'Liturgical service index'),el('p',{},'Browse traditional service categories. Available texts open in the existing reader; categories without texts are marked unavailable.'));
    const categories = [['Agpeya','agpeya'],['Midnight Praise and Psalmody','praises|psalmody'],['Raising of Incense','incense|vespers|matins'],['Divine Liturgies','liturgy|liturgies'],['Daily Readings','readings'],['Holy Pascha','pascha'],['Melodies','melodies'],['Antiphonary','antiphonary'],['Baptism','baptism'],['Crowning','crowning'],['Funeral services','funeral'],['Consecrations','consecration'],['Clergy prayers','clergy'],['Lakkan','lakkan'],['Unction of the sick','unction'],['Prostration','prostration'],['Veneration','veneration'],['Bible','bible']];
    for(const [label,pattern] of categories){
      const rx=new RegExp(pattern,'i');
      const matches=lib.home.map(h=>h.node?lib.nodes[h.node]:h).filter(n=>n&&rx.test((n.id||n.special||'')+' '+(n.title?.en||'')));
      const line=el('div',{style:'padding:8px 0;border-bottom:1px solid #8884'},el('strong',{},label));
      if(matches.length) for(const n of matches) line.append(el('div',{},el('a',{href:n.special?'#/'+n.special:'#/n/'+n.id},tt(n.title)||label)));
      else line.append(el('div',{style:'font-size:13px;opacity:.75'},'No verified text available in this category yet.'));
      guide.append(line);
    }
    const panel = el('section', { class: 'libpanel' },
      el('div', { class: 'libhead' }, el('h2', {}, t('library')),
        el('button', { class: 'ib', 'aria-label': t('bookmarks'), onclick: openBookmarks, html: '<svg viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4-6 4z"/></svg>' }),
        el('button', { class: 'ib', 'aria-label': t('search'), onclick: () => go('#/search/'), html: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/></svg>' })),
      tiles);
    navPage(masthead(false), el('div', { class: 'home-grid' }, card, panel, guide));
  }
  function todayButtons(holy) {
    const wrap = el('div');
    const add = (key, label) => {
      const n = Object.values(LIB.nodes).find(x => x.holy === key && x.id.startsWith(key === 'easter' ? 'resurrection' : 'pascha-'));
      if (n) { wrap.append(el('a', { class: 'tbtn', href: '#/n/' + n.id, onclick: e => e.stopPropagation() }, label + ': ' + tt(n.title))); wrap.append(' '); }
    };
    if (holy) add(holy, t('todaysService'));
    const NEXT_EVE = { palm: 'monday-eve', monday: 'tuesday-eve', tuesday: 'wednesday-eve', wednesday: 'thursday-eve', thursday: 'friday-eve', saturday: 'easter-eve' };
    if (holy && NEXT_EVE[holy]) add(NEXT_EVE[holy], t('tonight'));
    return wrap;
  }

  async function viewNode(nid) {
    const lib = await library();
    const n = lib.nodes[nid];
    if (!n) return go('#/');
    try { sessionStorage.setItem('lr.node', nid); } catch (e) { /* ignore */ }
    setBar('', {});
    const parent = parentOfNode(nid);
    const back = parent ? '#/n/' + parent.id : '#/';
    const title = lib.home.some(h => h.node === nid) ? t('cat_' + nid) : tt(n.title);
    const holy = CopticCal.season(nowJDN()).holy;
    let body;
    if (n.view === 'tiles') {
      body = el('div', { class: 'tiles' }, n.items.map(it => tileFor(itemInfo(it), n.icon)));
    } else {
      const links = el('div', { class: 'links' }, n.items.map(it => {
        const info = itemInfo(it);
        const g = CopticCal.jdnToGreg(nowJDN());
        const weekday = new Date(g.y, g.m - 1, g.d).getDay();
        const adam = weekday <= 2;
        const recommended = nid === 'cymbal-variants' && it.doc === (adam ? 'cymbal-variants-35' : 'cymbal-variants-32');
        const isToday = recommended || (info.holy && holy && info.holy === holy);
        return el('a', { href: info.href }, tt(info.title), isToday ? el('span', { class: 'tagt' }, t('today')) : null,
          null);
      }));
      body = el('div', { class: 'plist' }, el('div', { class: 'side' }, el('div', { class: 'art', html: iconOf(n.icon) })), links);
    }
    if (nid === 'seasonal-doxology-list') {
      const j = nowJDN(), g = CopticCal.jdnToGreg(j), se = CopticCal.seasonInfo(j), d = CopticCal.season(j).diff;
      const map = {'nayrouz':[2], 'cross':[12], 'kiahk':[32,46], 'nativity':[56], 'theophany':[68], 'lent':[new Date(g.y,g.m-1,g.d).getDay()===0?90:82], 'jonah':[163], 'circumcision':[160], 'transfiguration':[168]};
      const picks = d===-7?[110]:d===39?[141]:d===49?[151]:d>=0&&d<50?[121,131]:(map[se.key]||[]);
      const links = picks.map(n=>'seasonal-doxology-list-'+n).filter(id=>lib.docs[id]).map(id=>el('a',{href:'#/doc/'+id},tt(lib.docs[id].title)));
      body = el('div',{},el('section',{class:'libpanel',style:'padding:16px;margin-bottom:12px'},el('strong',{},gregText(j)),el('p',{},S.ui==='ar'?se.ar:se.en),el('h3',{},S.ui==='ar'?'اقتراحات موسمية':'Seasonal suggestions'),links.length?el('div',{class:'links'},links):el('p',{},S.ui==='ar'?'اختر من القائمة أدناه.':'Choose from the full list below.')),body);
    }
    if (nid === 'creation-litanies') {
      const j = nowJDN(), c = CopticCal.jdnToCoptic(j);
      const md = c.m * 100 + c.d;
      const seeds = md >= 210 && md < 510;
      const fruits = md >= 510 && md < 1012;
      const en = seeds ? 'Seeds and herbs' : fruits ? 'Fruits and air of heaven' : 'Waters of the rivers';
      const ar = seeds ? 'الزروع والعشب' : fruits ? 'الثمار وأهوية السماء' : 'مياه الأنهار';
      body = el('div',{},el('section',{class:'libpanel',style:'padding:16px;margin-bottom:12px'},
        el('strong',{},gregText(j)),el('p',{},copText(j)),
        el('h3',{},S.ui === 'ar' ? ar : en),
        el('p',{class:'note'},S.ui === 'ar' ? 'إرشاد موسمي؛ النصوص أدناه تشمل الطلبات مجتمعة.' : 'Seasonal guidance; the available texts below contain the combined petitions. Confirm local liturgical practice.')),body);
    }
    if (nid === 'fractions') {
      const j = nowJDN(), c = CopticCal.jdnToCoptic(j), season = CopticCal.seasonInfo(j), d = CopticCal.season(j).diff;
      const choices = [];
      const add = n => { const id = 'fraction-choice-' + n; if (lib.docs[id] && !choices.includes(id)) choices.push(id); };
      if (d === -7) add(94);
      else if (d >= 0 && d <= 49) add(99);
      else if (season.key === 'lent') add(89);
      else if (season.key === 'apostles-fast' || season.key === 'apostles') add(111);
      else if (season.key === 'transfiguration') add(117);
      else if (season.key === 'mary-fast' || season.key === 'assumption') { add(122); add(130); }
      else if (season.key === 'nayrouz') add(73);
      else if (season.key === 'nativity-fast' || season.key === 'nativity' || season.key === 'kiahk' || season.key === 'nativity-paramoun') add(79);
      else if (season.key === 'theophany') { add(82); add(86); }
      if (c.d === 29 && c.m <= 12) add(66);
      const panel = el('section', {class:'libpanel',style:'padding:16px;margin-bottom:12px'},
        el('strong', {}, gregText(j)), el('p', {}, S.ui === 'ar' ? season.ar : season.en),
        el('h3', {}, S.ui === 'ar' ? 'قسمات مناسبة للمناسبة' : 'Seasonal fraction suggestions'),
        el('p', {class:'note'}, S.ui === 'ar' ? 'اختيارات مقترحة وليست تحديداً إلزامياً للطقس.' : 'Suggestions only; confirm the applicable rite and feast with the service leader.'),
        choices.length ? el('div',{class:'links'},choices.map(id=>el('a',{href:'#/doc/'+id},tt(lib.docs[id].title)))) : el('p',{},S.ui === 'ar' ? 'اختر من القائمة الكاملة أدناه.' : 'Choose from the full list below.'));
      body = el('div', {}, panel, body);
    }
    if (nid === 'cymbal-variants') {
      const g = CopticCal.jdnToGreg(nowJDN());
      const adam = new Date(g.y, g.m - 1, g.d).getDay() <= 2;
      const intro = adam ? 'cymbal-variants-35' : 'cymbal-variants-32';
      body = el('div', {}, el('section', {class:'libpanel',style:'padding:16px;margin-bottom:12px'},
        el('strong', {}, gregText(nowJDN())),
        el('p', {}, S.ui === 'ar' ? (adam ? 'اللحن الآدمي' : 'اللحن الواطس') : (adam ? 'Adam introduction for selected day' : 'Watos introduction for selected day')),
        el('a', {href:'#/doc/'+intro}, S.ui === 'ar' ? 'افتح المقدمة' : 'Open recommended introduction'),
        el('p', {}, el('a', {href:'#/doc/cymbal-variants-40'}, S.ui === 'ar' ? 'التكملة المشتركة' : 'Open common continuation'))), body);
    }
    if(nid==='praises'){
      const seasonal=el('section',{class:'libpanel',style:'padding:16px;margin-top:12px'},el('h2',{},'Seasonal Psalis'));
      for(const name of ['Adam Nativity Paramoun Psali on the Sunday Theotokia','Adam Psali for Thomas Sunday']){
        seasonal.append(el('div',{style:'padding:12px 0;border-bottom:1px solid #8884'},el('strong',{},name),el('div',{class:'note'},'Prayer text awaiting verified transcription.')));
      }
      body=el('div',{},body,seasonal);
    }
    navPage(masthead(true), navPanel(title, back, body));
  }

  const BIBLE_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
    'Ezra', 'Nehemiah', 'Tobit', 'Judith', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes', 'Song of Songs', 'Wisdom', 'Sirach', 'Isaiah', 'Jeremiah', 'Lamentations', 'Baruch',
    'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts',
    'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon',
    'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'];
  const FULL_BOOK = { Psalms: 'psalms-449', Revelation: 'saturday-579' };
  async function viewBible(book) {
    await library();
    setBar('', {});
    const data = await getJSON('data/scripture.json');
    if (!book) {
      const have = new Set(data.map(e => e.book));
      const links = el('div', { class: 'links' }, BIBLE_BOOKS.map(b => el('a', { href: '#/bible/' + encodeURIComponent(b), class: (have.has(b) || FULL_BOOK[b]) ? '' : 'dim' }, b)));
      navPage(masthead(true), navPanel(t('cat_bible'), '#/', el('div', { class: 'plist' }, el('div', { class: 'side' }, el('div', { class: 'art', html: iconOf('bible') })), links)));
      return;
    }
    const items = [];
    if (FULL_BOOK[book]) items.push(el('a', { href: '#/doc/' + FULL_BOOK[book] }, '★ ' + tt(LIB.docs[FULL_BOOK[book]].title)));
    for (const e of data.filter(e => e.book === book)) items.push(el('a', { href: `#/doc/${e.doc}?r=${e.row}` }, e.ref, el('small', { style: 'direction:ltr;font-family:var(--ui);font-size:13px' }, tt(e.title))));
    if (!items.length) items.push(el('p', { class: 'note', style: 'text-align:start' }, t('noOccReadings')));
    navPage(masthead(true), navPanel(book, '#/bible', el('div', { class: 'plist' }, el('div', { class: 'side' }, el('div', { class: 'art', html: iconOf('bible') })), el('div', { class: 'links' }, items))));
  }

  // ------------------------------------------------------------------ document
  async function viewDoc(id, rowFocus) {
    await library();
    view.replaceChildren(el('div', { class: 'empty' }, t('loading')));
    const res = await loadDoc(id);
    if (!res) { view.replaceChildren(el('div', { class: 'empty' }, t('noResults'))); return; }
    current = { id, title: res.sec.title, rows: prepareRows(res.sec.rows), cols: [], node: nodeOfDoc(id) };
    setBar(tt(res.sec.title), { back: true, doc: true });
    updateBookmarkIcon();
    try { localStorage.setItem('lr.last', '#/doc/' + id); } catch (e) { /* ignore */ }
    renderDoc();
    buildToc();
    if (rowFocus != null) {
      const r = view.querySelector(`.row[data-i="${rowFocus}"]`);
      if (r) { r.scrollIntoView({ block: 'center' }); r.classList.add('flash'); }
    }
    if (S.mode === 'slides' && rowFocus == null) presentOpen(0, false);
  }

  function renderDoc() {
    const { rows, title } = current;
    const vis = rows.filter(roleVisible);
    const cols = activeCols(vis);
    current.cols = cols;
    const stack = useStack(cols);
    const tpl = gridTemplate(cols);
    const head = el('div', { class: 'dhead' }, el('div', { class: 't' }, title.en), el('div', { class: 'a', dir: 'rtl' }, title.ar));
    const hdr = el('div', { class: 'colhdr', style: `grid-template-columns:${tpl}` }, cols.map(c => el('span', { class: RTL_COLS.has(c) ? 'rtl' : '' }, t('col_' + c))));
    const list = el('div', { class: 'rows' });
    const frag = document.createDocumentFragment();
    for (const r of vis) {
      const row = el('div', { class: 'row' + (r.kind ? ' ' + r.kind : '') + (r.cls ? ' ' + r.cls : ''), style: `grid-template-columns:${tpl}`, 'data-i': r._i });
      if (r.img) { if (S.slides) row.append(el('div', { class: 'slideimg' }, el('img', { src: r.img, alt: '', loading: 'lazy' }))); else continue; }
      if (r.kind === 'role') { cols.forEach(c => row.append(cellFor(r, c))); frag.append(row); continue; }
      if (r.kind === 'heading') {
        row.setAttribute('role', 'button');
        row.setAttribute('tabindex', '0');
        row.setAttribute('aria-expanded', 'true');
        row.title = S.ui === 'ar' ? 'اضغط للطي أو التوسيع' : 'Tap to collapse or expand this prayer';
        row.onclick = () => toggleSection(row);
        row.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSection(row); } };
      }
      const has = cols.some(c => hasCol(r, c));
      if (has) {
        const cells = cols.map(c => cellFor(r, c));
        const empty = cells.map(d => !d.textContent.trim() && !d.querySelector('img'));
        if (!stack && empty.some(Boolean) && empty.some(e => !e)) {
          let last = -1;
          const span = cells.map(() => 1);
          const keep = cells.map(() => false);
          for (let k = 0; k < cells.length; k++) {
            if (!empty[k]) { last = k; continue; }
            // an empty column is taken by the text on its left (keeps every language in its own column)
            if (last >= 0 && !RTL_COLS.has(cols[last])) span[last]++;
            else {
              const right = cells.findIndex((d, j) => j > k && !empty[j]);
              if (last < 0 || right < 0 || !RTL_COLS.has(cols[right])) keep[k] = true; else span[right]++;
            }
          }
          cells.forEach((d, k) => { if (!empty[k]) { if (span[k] > 1) d.style.gridColumn = 'span ' + span[k]; row.append(d); } else if (keep[k]) row.append(el('div', { class: 'cell ' + cols[k] })); });
        } else cells.forEach(d => row.append(d));
      } else if (!r.img) continue;
      frag.append(row);
    }
    list.append(frag);
    const container = el('div', { class: stack ? 'stack' : '' }, hdr, list);
    const order = nodeDocs(current.node);
    const k = order.indexOf(current.id);
    const prev = order[k - 1], next = order[k + 1];
    const pager = el('div', { class: 'pager' },
      prev ? el('a', { href: '#/doc/' + prev }, el('small', {}, '‹ ' + t('prev')), tt(LIB.docs[prev].title)) : el('span'),
      next ? el('a', { class: 'nx', href: '#/doc/' + next }, el('small', {}, t('next') + ' ›'), tt(LIB.docs[next].title)) : el('span'));
    const notes = [];
    if (cols.some(c => ['cop_lat', 'cop_ar', 'ar_lat', 'en_ar'].includes(c))) notes.push(t('phonApprox'));
    if (cols.includes('cop') && rows.some(r => r.cop_img && r.cop_img.length)) notes.push(S.copScan ? t('copticImg') : t('copOcrNote'));
    if (rows.some(r => r.cls === 'bgref')) notes.push('NKJV passage panels appear inline. Bible Gateway may restrict embedding on other websites.');
    view.replaceChildren(head, container, notes.length ? el('p', { class: 'note' }, notes.join(' ')) : '', pager);
    linkVerses();
    for (const h of list.querySelectorAll('.row.heading')) {
      const r = rows.find(x => String(x._i) === h.dataset.i);
      if (r && /^(?:\\*\\*\\s*)?(?:if a pope, metropolitan or bishop is present|introduction in the presence of the pope, metropolitan or bishop|\\[optional\\])/i.test((r.en || '').trim())) toggleSection(h);
    }
    window.scrollTo(0, 0);
  }
  // Scripture stays within the liturgy flow. Bible Gateway can block
  // third-party framing; never claim that an unavailable passage has loaded.
  function linkVerses() {
    document.querySelectorAll('.row.bgref').forEach(row => {
      if (row.dataset.scriptureInline) return;
      row.dataset.scriptureInline = '1';
      // Normalize *every* reading reference before sending it to Bible Gateway.
      // The old regular expression was double-escaped and left "(NKJV)" in search.
      const raw = (row.textContent || '').trim();
      const label = raw
        .replace(/\s*\(\s*NKJV\s*\)/gi, '')
        .replace(/\s*[—–-]\s*NKJV\b/gi, '')
        .replace(/\s+/g, ' ')
        .trim();
      if (!label) return;
      row.textContent = label + ' (NKJV)';
      const section = document.createElement('section');
      section.className = 'scripture-inline';
      section.style.cssText = 'display:block;margin:8px 0 22px;padding:14px;background:#080808;color:#f3d58f;border-left:2px solid #92743b';
      const title = document.createElement('div');
      title.textContent = label;
      title.style.cssText = 'font-size:1.1em;font-weight:bold;margin-bottom:10px';
      const iframe = document.createElement('iframe');
      iframe.title = 'Bible Gateway NKJV passage: ' + label;
      iframe.loading = 'lazy';
      iframe.referrerPolicy = 'no-referrer-when-downgrade';
      iframe.src = 'https://www.biblegateway.com/passage/?search=' + encodeURIComponent(label) + '&version=NKJV';
      iframe.style.cssText = 'width:100%;height:460px;border:1px solid #554629;background:white;color:black';
      const warning = document.createElement('p');
      warning.textContent = 'If Bible Gateway blocks embedded reading, the passage cannot be displayed here through an iframe. The reference above is still correct; an authorised embeddable Bible source is needed for reliable inline NKJV text.';
      warning.style.cssText = 'font-size:0.8em;opacity:.8;margin:8px 0 0';
      section.append(title, iframe, warning);
      row.insertAdjacentElement('afterend', section);
    });
  }
  function toggleSection(hrow) {
    const closed = hrow.classList.toggle('closed');
    hrow.setAttribute('aria-expanded', String(!closed));
    let n = hrow.nextElementSibling;
    while (n && !n.classList.contains('heading')) { n.classList.toggle('collapsed', closed); n = n.nextElementSibling; }
  }
  function buildToc() {
    $('#tocTitle').textContent = tt(current.title);
    const list = $('#tocList'); list.replaceChildren();
    const heads = current.rows.filter(r => r.kind === 'heading');
    for (const h of heads) list.append(el('a', { href: '#', onclick: e => { e.preventDefault(); closeAll(); const r = view.querySelector(`.row[data-i="${h._i}"]`); if (r) { r.scrollIntoView({ block: 'start' }); window.scrollBy(0, -90); r.classList.add('flash'); } } }, h.en || h.ar || ''));
    if (current.node) {
      list.append(el('div', { class: 'sh', style: 'margin-top:10px' }, tt(current.node.title)));
      for (const d of nodeDocs(current.node)) list.append(el('a', { href: '#/doc/' + d, class: d === current.id ? 'cur' : '', onclick: closeAll }, tt(LIB.docs[d].title)));
    }
  }

  // ------------------------------------------------------------------ bookmarks
  const getBM = () => { try { return JSON.parse(localStorage.getItem('lr.bookmarks') || '[]'); } catch (e) { return []; } };
  const setBM = b => { try { localStorage.setItem('lr.bookmarks', JSON.stringify(b)); } catch (e) { /* ignore */ } };
  function updateBookmarkIcon() { $('#btnBookmark').classList.toggle('on', getBM().some(b => b.id === current.id)); }
  function toggleBookmark() {
    let b = getBM();
    if (b.some(x => x.id === current.id)) b = b.filter(x => x.id !== current.id); else b.push({ id: current.id });
    setBM(b); updateBookmarkIcon();
  }
  function openBookmarks() {
    const card = $('#modalCard');
    const draw = () => {
      const b = getBM();
      card.replaceChildren(
        el('div', { class: 'mhead' }, el('span', {}, t('bookmarks')), el('button', { class: 'ib', onclick: closeAll, html: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>' })),
        el('p', { class: 'mhint' }, t('bookmarksHint')),
        ...(b.length ? b.map((x, i) => el('div', { class: 'bm' },
          el('a', { href: '#/doc/' + x.id, onclick: closeAll }, LIB.docs[x.id] ? tt(LIB.docs[x.id].title) : x.id),
          el('button', { disabled: i === 0, onclick: () => { [b[i - 1], b[i]] = [b[i], b[i - 1]]; setBM(b); draw(); } }, '↑'),
          el('button', { disabled: i === b.length - 1, onclick: () => { [b[i + 1], b[i]] = [b[i], b[i + 1]]; setBM(b); draw(); } }, '↓'),
          el('button', { 'aria-label': t('removeBookmark'), onclick: () => { b.splice(i, 1); setBM(b); draw(); } }, '🗑'))) : [el('p', { class: 'empty' }, t('noBookmarks'))]));
    };
    draw();
    $('#modal').classList.add('on'); $('#scrim').classList.add('on');
  }

  // ------------------------------------------------------------------ date / occasion
  function viewDate() {
    setBar(t('selectDate'), { back: true, keep: true });
    const j = nowJDN();
    const pick = el('input', { type: 'date', value: (() => { const g = CopticCal.jdnToGreg(j); return `${g.y}-${String(g.m).padStart(2, '0')}-${String(g.d).padStart(2, '0')}`; })(),
      onchange: e => { const [y, m, d] = e.target.value.split('-').map(Number); if (y) { S.fixedJdn = CopticCal.gregToJDN(y, m, d); save(); go('#/'); } } });
    const live = el('a', { class: 'li', href: '#/', onclick: () => { S.fixedJdn = null; save(); } }, el('span', { class: 't' }, (S.fixedJdn ? '' : '✓ ') + t('live')), el('span', { class: 'a' }, gregText(CopticCal.todayJDN())));
    const occ = CopticCal.occasions(j).map(o => el('a', { class: 'li', href: '#/', onclick: () => { S.fixedJdn = o.jdn; save(); } },
      el('span', { class: 't' }, (S.fixedJdn === o.jdn ? '✓ ' : '') + (S.ui === 'ar' ? o.ar : o.en)), el('span', { class: 'a', style: 'direction:ltr;font-family:var(--ui);font-size:13px' }, gregText(o.jdn) + ' · ' + copText(o.jdn))));
    view.replaceChildren(el('h2', { class: 'ctitle' }, t('selectDate')), el('div', { class: 'list' }, live, el('div', { class: 'li' }, el('span', { class: 't' }, t('selectDate')), pick)),
      el('h2', { class: 'ctitle' }, t('selectOccasion')), el('div', { class: 'list' }, occ));
  }

  // readings for the selected day
  const SEASON_KEYWORDS = { kiahk: ['KIAHK'], 'nativity-fast': ['KIAHK'], nativity: ['NATIVITY'], 'nativity-paramoun': ['NATIVITY'], theophany: ['EPIPHANY'], 'theophany-paramoun': ['EPIPHANY'],
    lent: ['LENT'], jonah: ['JONAH'], palm: ['PALM'], holy: [], easter: ['RESURRECTION'], pentecost50: ['RESURRECTION'], ascension: ['ASCENSION'], pentecost: ['PENTECOST'],
    cross: ['CROSS'], nayrouz: ['NEW YEAR'], 'apostles-fast': ['APOSTLES'], apostles: ['APOSTLES'], 'mary-fast': ['SAINT MARY'], transfiguration: ['TRANSFIGURATION'], cana: ['CANA'],
    circumcision: ['CIRCUMCISION'], presentation: ['TEMPLE'] };
  async function viewOccasion() {
    const lib = await library();
    setBar(t('occReadings'), { back: true, keep: true });
    const j = nowJDN();
    const se = CopticCal.seasonInfo(j), holy = CopticCal.season(j).holy;
    const out = [el('h2', { class: 'ctitle' }, (S.ui === 'ar' ? se.ar : se.en)), el('p', { class: 'note', style: 'text-align:start;padding:0 16px' }, copText(j) + ' · ' + gregText(j))];
    const items = [];
    if (holy) {
      const n = Object.values(lib.nodes).find(x => x.holy === holy && x.id.startsWith(holy === 'easter' ? 'resurrection' : 'pascha-'));
      const docsOf = nd => nd.items.flatMap(x => x.doc ? [x.doc] : x.node ? docsOf(lib.nodes[x.node]) : []);
      if (n) for (const d of docsOf(n)) items.push(el('a', { class: 'li', href: '#/doc/' + d }, el('span', { class: 't' }, tt(lib.docs[d].title))));
    }
    if (holy && holy !== 'easter') {
      out.push(el('p', { class: 'note', style: 'padding:12px 16px' }, 'Holy Pascha uses its own day-and-hour services, not the ordinary Katamaros weekday readings. Covenant Thursday and Bright Saturday retain their appointed special services.'));
      if (items.length) out.push(el('h2', { class: 'ctitle' }, 'Holy Pascha services'), el('div', { class: 'list' }, items));
      out.push(el('div', { class: 'pad' }, el('a', { class: 'btn', href: '#/n/pascha' }, 'Browse Holy Pascha'), ' ', el('a', { class: 'btn', href: '#/date' }, t('selectDate'))));
      view.replaceChildren(...out); return;
    }
    if (items.length) out.push(el('div', { class: 'list' }, items));
    // the day's Katameros readings and Synaxarium, linking to Readings > Vespers / Matins / Liturgy
    const R = await readingsFor(j);
    if (!R.pascha) {
      const fmt = r => r ? r.book + ' ' + r.ref : '—';
      const line = (label, doc, r) => el('a', { class: 'li', href: '#/doc/' + doc }, el('span', { class: 't' }, label), el('span', { class: 'a', style: 'direction:ltr;font-family:var(--ui);font-size:14px' }, fmt(r)));
      out.push(el('h2', { class: 'ctitle' }, (R.occasion || R.day?.occasion || t('occReadings'))));
      if (R.missing) out.push(el('p', { class: 'note', style: 'padding:0 16px' }, (R.missing === 'lent' ? 'Great Lent weekday readings need the Katameros of Great Lent.' : 'Holy Fifty Days weekday readings need the Katameros of the Holy Fifty Days.') + ' It is not in the library yet.'));
      else {
        const v = R.vespers || {}, m = R.matins || {}, l = R.liturgy || {};
        out.push(el('div', { class: 'list' },
          line('Vespers Psalm', 'rd-v-pg', v.psalm), line('Vespers Gospel', 'rd-v-pg', v.gospel),
          line('Matins Psalm', 'rd-m-pg', m.psalm), line('Matins Gospel', 'rd-m-pg', m.gospel),
          line('Pauline Epistle', 'rd-l-pauline', l.pauline), line('Catholic Epistle', 'rd-l-catholic', l.catholic),
          line('Praxis', 'rd-l-acts', l.acts), line('Liturgy Psalm', 'rd-l-pg', l.psalm), line('Liturgy Gospel', 'rd-l-pg', l.gospel)));
      }
      const c = CopticCal.jdnToCoptic(j);
      const syn = (await getJSON('data/synaxarium.json')).days[c.m + '-' + c.d];
      if (syn) out.push(el('h2', { class: 'ctitle' }, 'Synaxarion'), el('div', { class: 'list' }, syn.titles.map(x => el('a', { class: 'li', href: '#/doc/rd-l-synax' }, el('span', { class: 't' }, x)))));
      if (R.src) out.push(el('p', { class: 'note', style: 'padding:0 16px' }, R.src));
    }
    // seasonal texts from the doxologies / responses / hymns
    const kws = SEASON_KEYWORDS[se.key] || [];
    const seasonal = [];
    for (const did of ['dc-seasonal-doxologies', 'dc-seasonal-responses', 'dc-holy-communion-seasonal-hymns']) {
      const m = lib.docs[did];
      for (const [i, h] of m.heads) if (kws.some(k => h.toUpperCase().includes(k))) seasonal.push(el('a', { class: 'li', href: `#/doc/${did}?r=${i}` }, el('span', { class: 't' }, h), el('span', { class: 'a', style: 'direction:ltr' }, tt(m.title))));
    }
    if (seasonal.length) out.push(el('h2', { class: 'ctitle' }, t('seasonalTexts')), el('div', { class: 'list' }, seasonal));
    out.push(el('div', { class: 'pad' }, el('a', { class: 'btn', href: '#/scripture-index' }, t('scriptureIndex')), ' ', el('a', { class: 'btn', href: '#/date' }, t('selectDate'))));
    view.replaceChildren(...out);
  }

  async function viewScripture() {
    setBar(t('scriptureIndex'), { back: true, keep: true });
    const data = await getJSON('data/scripture.json');
    const lib = await library();
    const inp = el('input', { type: 'search', placeholder: t('filter') });
    const box = el('div', { class: 'list' });
    const draw = () => {
      const q = inp.value.trim().toLowerCase();
      box.replaceChildren();
      let lastBook = null;
      for (const e of data) {
        if (q && !e.ref.toLowerCase().includes(q) && !tt(e.title).toLowerCase().includes(q)) continue;
        if (e.book !== lastBook) { box.append(el('div', { class: 'sh' }, e.book)); lastBook = e.book; }
        box.append(el('a', { class: 'li', href: `#/doc/${e.doc}?r=${e.row}` }, el('span', { class: 't' }, e.ref), el('span', { class: 'a', style: 'direction:ltr;font-family:var(--ui);font-size:13px' }, tt(e.title))));
      }
    };
    inp.oninput = draw; draw();
    view.replaceChildren(el('div', { class: 'sbox' }, inp), box);
  }

  async function viewIndex() {
    const lib = await library();
    setBar(t('indexTitle'), { back: true, keep: true });
    const inp = el('input', { type: 'search', placeholder: t('filter') });
    const entries = [];
    for (const [id, m] of Object.entries(lib.docs)) {
      if (m.parent) { entries.push({ k: tt(m.title), href: '#/doc/' + id, sub: tt(lib.docs[m.parent].title) }); continue; }
      entries.push({ k: tt(m.title), href: '#/doc/' + id, sub: '' });
      for (const [i, h0] of m.heads) {
        const h = h0.replace(/^[^A-Za-z\u0600-\u06ff\u2c80-\u2cff]+/, '').replace(/[\s\-:]+$/, '').trim();
        if ((h.match(/[A-Za-z\u0600-\u06ff]/g) || []).length < 4) continue;
        if ((h.match(/[A-Za-z\u0600-\u06ff\s,'’()&.]/g) || []).length / h.length < 0.85) continue;
        const k = h === h.toUpperCase() ? h.charAt(0) + h.slice(1).toLowerCase().replace(/\b(god|lord|christ|jesus|mary|holy|spirit|saint|st|our|virgin|archangel|michael|john|mark|george|pope|bishop|cross|nativity|kiahk|lent|resurrection|pentecost|epiphany)\b/g, w => w.charAt(0).toUpperCase() + w.slice(1)) : h;
        entries.push({ k, href: `#/doc/${id}?r=${i}`, sub: tt(m.title) });
      }
    }
    entries.sort((a, b) => a.k.localeCompare(b.k));
    const box = el('div', { class: 'list' });
    const draw = () => {
      const q = inp.value.trim().toLowerCase();
      box.replaceChildren();
      let letter = null, n = 0;
      for (const e of entries) {
        if (q && !e.k.toLowerCase().includes(q) && !e.sub.toLowerCase().includes(q)) continue;
        const L = (e.k.match(/[A-Za-z؀-ۿ]/) || ['#'])[0].toUpperCase();
        if (L !== letter) { box.append(el('div', { class: 'sh' }, L)); letter = L; }
        box.append(el('a', { class: 'li', href: e.href }, el('span', { class: 't' }, e.k), el('span', { class: 'a', style: 'direction:ltr;font-family:var(--ui);font-size:13px' }, e.sub)));
        if (++n > 1500) break;
      }
    };
    inp.oninput = draw; draw();
    view.replaceChildren(el('div', { class: 'sbox' }, inp), box);
  }

  // ------------------------------------------------------------------ search
  let searchIdx = null;
  async function buildIndex() {
    if (searchIdx) return searchIdx;
    const lib = await library();
    const files = [...new Set(Object.values(lib.docs).filter(m => m.file).map(m => m.file))];
    const idx = [];
    for (const f of files) {
      const d = await getJSON('data/' + f);
      for (const s of d.sections) if (lib.docs[s.id]) s.rows.forEach((r, i) => { if (r.en || r.ar || r.cop) idx.push({ s: s.id, st: s.title, i, en: r.en || '', ar: r.ar || '', cop: r.cop || '' }); });
    }
    return (searchIdx = idx);
  }
  const normAr = s => s.replace(/[ً-ْـ]/g, '').replace(/[أإآ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه');
  const normCop = s => s.normalize('NFD').replace(/[̀̅]/g, '').toLowerCase();
  async function viewSearch(q) {
    setBar(t('search'), { back: true, keep: true });
    const input = el('input', { type: 'search', placeholder: t('searchPh'), value: q || '' });
    const out = el('div');
    const form = el('form', { class: 'sbox', onsubmit: e => { e.preventDefault(); go('#/search/' + encodeURIComponent(input.value.trim())); } }, input, el('button', { class: 'btn' }, t('search')));
    view.replaceChildren(form, out);
    if (!q) { input.focus(); return; }
    out.append(el('div', { class: 'empty' }, t('loading')));
    const idx = await buildIndex();
    const isAr = /[؀-ۿ]/.test(q), isCop = /[Ⲁ-⳿Ϣ-ϯ]/.test(q);
    const nq = isAr ? normAr(q) : isCop ? normCop(q) : q.toLowerCase();
    const hits = [];
    for (const e of idx) {
      const hay = isAr ? normAr(e.ar) : isCop ? normCop(e.cop) : e.en.toLowerCase();
      const k = hay.indexOf(nq);
      if (k >= 0) { hits.push([e, k]); if (hits.length >= 300) break; }
    }
    out.replaceChildren();
    if (!hits.length) { out.append(el('div', { class: 'empty' }, t('noResults'))); return; }
    out.append(el('p', { class: 'note', style: 'text-align:start' }, `${t('resultsFor')} “${q}”: ${hits.length}${hits.length >= 300 ? '+' : ''}`));
    for (const [e, k] of hits) {
      const src = isAr ? e.ar : isCop ? e.cop : e.en;
      const a = Math.max(0, k - 70), z = Math.min(src.length, k + nq.length + 110);
      let snip = esc(src.slice(a, z));
      if (!isAr && !isCop) snip = esc(src.slice(a, k)) + '<mark>' + esc(src.slice(k, k + nq.length)) + '</mark>' + esc(src.slice(k + nq.length, z));
      out.append(el('a', { class: 'hit', href: `#/doc/${e.s}?r=${e.i}` }, el('small', {}, tt(e.st)), el('div', { class: 'x' + (isAr ? ' rtl' : '') + (isCop ? ' copt' : ''), html: (a > 0 ? '… ' : '') + snip + (z < src.length ? ' …' : '') })));
    }
  }

  // ------------------------------------------------------------------ settings (Coptic Reader-style list)
  function renderSettings() {
    $('#setTitle').textContent = t('settings');
    const body = $('#setBody'); body.replaceChildren();
    const refresh = () => { save(); applyTheme(); renderSettings(); rerender(); };
    const seg = (opts, val, set) => el('div', { class: 'seg' }, opts.map(([v, label]) => el('button', { class: v === val ? 'on' : '', onclick: () => { set(v); refresh(); } }, label)));
    const row = (label, hint, ...ctrl) => el('div', { class: 'sr' }, el('div', { class: 'lb' }, label), hint ? el('div', { class: 'hn' }, hint) : null, ...ctrl);
    const chk = (label, val, set) => el('label', { class: 'chk' }, el('input', { type: 'checkbox', checked: !!val, onchange: e => { set(e.target.checked); save(); applyTheme(); rerender(); } }), label);
    body.append(el('div', { class: 'sh' }, t('appLang')), row(t('appLang'), null, seg(UI_LANGS, S.ui, v => S.ui = v)));
    body.append(el('div', { class: 'sh' }, t('presentMode')), row(t('presentMode'), t('pmHint'), seg([['scroll', t('pm_scroll')], ['slides', t('pm_slides')]], S.mode, v => S.mode = v)));
    body.append(el('div', { class: 'sh' }, t('scrollOpts')),
      row(t('docTheme'), null, seg([['book', t('th_book')], ['night', t('th_night')], ['light', t('th_light')], ['sepia', t('th_sepia')]], S.theme, v => S.theme = v)),
      row(t('textSize') + ' [' + S.fs + ']', null, el('input', { type: 'range', min: 12, max: 44, value: S.fs, oninput: e => { S.fs = +e.target.value; applyTheme(); save(); e.target.parentNode.firstChild.textContent = t('textSize') + ' [' + S.fs + ']'; } })),
      row(t('showComments'), t('commentsHint'), chk(t('showComments'), S.comments, v => S.comments = v)));
    const langs = row(t('showLangs'), t('langsHint'));
    S.order.forEach((c, i) => langs.append(el('div', { class: 'colopt' }, chk(t('col_' + c), S.on[c], v => S.on[c] = v),
      el('button', { class: 'mv', disabled: i === 0, onclick: () => { [S.order[i - 1], S.order[i]] = [S.order[i], S.order[i - 1]]; refresh(); } }, '↑'),
      el('button', { class: 'mv', disabled: i === S.order.length - 1, onclick: () => { [S.order[i + 1], S.order[i]] = [S.order[i], S.order[i + 1]]; refresh(); } }, '↓'))));
    body.append(langs);
    const commemorations = ['Holy Cross','Archangel Michael','Archangel Gabriel','Archangel Raphael','St. Joseph the Carpenter','St. John the Baptist','St. Peter and St. Paul','St. John the Evangelist','St. Stephen','St. Mark the Apostle','St. George','St. Mena','St. Demiana','St. Marina','St. Anthony the Great','St. Paul the Hermit','St. Macarius the Great','St. Moses the Strong','St. Bishoy','St. Shenute','St. Athanasius','St. Cyril of Alexandria','St. Mary of Egypt','St. Simon the Tanner','Pope Kyrillos VI','St. Habib Girgis','All Saints'];
    if (!Array.isArray(S.commemorations)) S.commemorations = [];
    const commList = el('div', {style:'max-height:280px;overflow:auto'});
    const filter = el('input',{type:'search',placeholder:'Search saints',style:'width:100%;padding:8px'});
    const showComms = () => { commList.replaceChildren(...commemorations.filter(n=>n.toLowerCase().includes(filter.value.toLowerCase())).map(n=>chk(n,S.commemorations.includes(n),v=>{S.commemorations=S.commemorations.filter(x=>x!==n);if(v)S.commemorations.push(n);}))); };
    filter.addEventListener('input',showComms);showComms();
    body.append(el('div',{class:'sh'},'Annual commemorations'),row('Church intercessors','Save your preferred commemorations on this device. This selection does not yet insert saint-specific hymns into services.',filter,commList));

    body.append(row(t('showRoles'), t('rolesHint'), ROLES.map(r => chk(t('role_' + r), S.roles[r], v => S.roles[r] = v))));
    body.append(row(t('layout'), null, seg([['auto', t('lay_auto')], ['side', t('lay_side')], ['stack', t('lay_stack')]], S.layout, v => S.layout = v)));
    body.append(el('div', { class: 'sh' }, t('phonetics')),
      row(t('phonetics'), t('phonApprox'), chk(t('useBookPhon'), S.bookPhon, v => S.bookPhon = v), chk(t('copScan'), S.copScan, v => S.copScan = v)));
    const hours = [[0, t('midnight')], [15, '3:00 PM'], [16, '4:00 PM'], [17, '5:00 PM'], [18, '6:00 PM'], [19, '7:00 PM'], [20, '8:00 PM']];
    body.append(el('div', { class: 'sh' }, t('general')),
      row(t('dayStart'), t('dayStartHint'), el('select', { onchange: e => { S.dayStart = +e.target.value; save(); rerender(); } }, hours.map(([v, l]) => el('option', { value: v, selected: S.dayStart === v ? true : null }, l)))),
      row(t('selectDate'), (S.fixedJdn ? gregText(S.fixedJdn) : t('live')), el('a', { class: 'btn', href: '#/date', onclick: closeAll }, t('selectOccasion'))),
      row(t('scripture'), null, el('span', { class: 'badge' }, t('nkjv'))),
      el('div', { class: 'sr' }, el('button', { class: 'btn', onclick: () => { S = JSON.parse(JSON.stringify(DEFAULTS)); refresh(); } }, t('reset'))));
  }
  function rerender() { if (current.id && location.hash.startsWith('#/doc/')) renderDoc(); else route(); }

  // ------------------------------------------------------------------ drawers
  function openDrawer(id) { closeAll(); $('#' + id).classList.add('open'); $('#' + id).setAttribute('aria-hidden', 'false'); $('#scrim').classList.add('on'); }
  function closeAll() {
    for (const d of document.querySelectorAll('.drawer')) { d.classList.remove('open'); d.setAttribute('aria-hidden', 'true'); }
    $('#modal').classList.remove('on'); $('#scrim').classList.remove('on');
  }

  // ------------------------------------------------------------------ slide show
  let pIdx = 0, pRows = [];
  function presentOpen(startRow = 0, full = true) {
    pRows = current.rows.filter(r => roleVisible(r) && !(r.kind === 'rubric' && (!S.comments || /scripture passage is displayed below its reference/i.test(r.en || ''))) && (r.img || r.kind === 'role' || r.kind === 'heading' || current.cols.some(c => hasCol(r, c))));
    // merge role markers into the following slide
    pIdx = Math.max(0, pRows.findIndex(r => r._i >= startRow));
    $('#present').classList.add('on');
    if (full) { const pe = $('#present'); if (pe.requestFullscreen) pe.requestFullscreen().catch(() => {}); }
    presentShow();
  }
  function presentShow() {
    const stage = $('#presentStage');
    stage.replaceChildren();
    let r = pRows[pIdx];
    if (!r) return;
    const cols = current.cols;
    stage.style.gridTemplateColumns = gridTemplate(cols);
    let roleRow = null;
    if (r.kind === 'role' && pRows[pIdx + 1]) { roleRow = r; }
    if (roleRow) { stage.append(el('div', { class: 'p-role' }, roleLabel(roleRow.role, 'en') + '  ' + roleLabel(roleRow.role, 'cop') + '  ' + roleLabel(roleRow.role, 'ar'))); r = pRows[pIdx + 1]; }
    else if (r._role && r.kind !== 'heading') stage.append(el('div', { class: 'p-role' }, roleLabel(r._role, 'en') + '  ' + roleLabel(r._role, 'cop') + '  ' + roleLabel(r._role, 'ar')));
    if (r.cls === 'bgref') {
      // Scripture slides must contain the passage viewer, not a reference-only
      // slide or the explanatory rubric from the scrolling document.
      const ref = (r.en || '').replace(/\\s*\\(\\s*NKJV\\s*\\)/gi, '').trim();
      stage.style.gridTemplateColumns = 'minmax(0,1fr)';
      const frame = el('iframe', {
        title: 'Scripture: ' + ref,
        src: 'https://www.biblegateway.com/passage/?search=' + encodeURIComponent(ref) + '&version=NKJV',
        loading: 'eager',
        style: 'width:100%;height:100%;min-height:65vh;max-height:85vh;border:1px solid #6b542a;background:#fff;border-radius:4px;'
      });
      const container = el('div', { style: 'grid-column:1/-1;display:flex;flex-direction:column;width:100%;height:80vh;min-height:0;gap:8px;padding:8px 12px;box-sizing:border-box;' },
        el('div', { style: 'color:#f3d58f;font-size:clamp(16px,2vw,28px);font-weight:bold;text-align:center;' }, ref + ' (NKJV)'),
        frame);
      stage.append(container);
      $('#pCount').textContent = `${pIdx + 1} / ${pRows.length}`;
      return;
    }
    if (r.img) stage.append(el('div', { class: 'slideimg', style: 'grid-column:1/-1;text-align:center' }, el('img', { src: r.img, alt: '' })));
    else if (r.kind === 'heading') { const h = el('div', { class: 'p-head' }); cols.forEach(c => { const d = cellFor(r, c); if (d.textContent.trim()) h.append(d); }); stage.append(h); }
    else {
      const wrap = r.kind === 'rubric' ? el('div', { class: 'p-rubric', style: 'display:contents' }) : null;
      cols.forEach(c => { const d = cellFor(r, c); (wrap || stage).append(d); });
      if (wrap) stage.append(wrap);
    }
    $('#pCount').textContent = `${pIdx + 1} / ${pRows.length}`;
    fitStage(stage);
  }
  function fitStage(stage) {
    let size = Math.min(window.innerWidth / (Math.max(1, current.cols.length) * 9), window.innerHeight / 8.5);
    const cells = stage.querySelectorAll('.cell');
    for (let k = 0; k < 45; k++) {
      cells.forEach(c => { c.style.fontSize = (c.classList.contains('ar') || c.classList.contains('cop_ar') || c.classList.contains('en_ar') ? size * 1.08 : size) + 'px'; });
      if (stage.scrollHeight <= stage.clientHeight + 2 || size < 13) break;
      size *= 0.93;
    }
  }
  function presentStep(d) {
    let n = pIdx + d;
    if (pRows[pIdx] && pRows[pIdx].kind === 'role' && d > 0) n = pIdx + 2;
    if (d < 0 && pRows[n - 1] && pRows[n - 1].kind === 'role') n = n - 1;
    if (n >= pRows.length) { presentEnd(); return; }
    pIdx = Math.max(0, n); presentShow();
  }
  function presentEnd() {
    const order = nodeDocs(current.node);
    const next = order[order.indexOf(current.id) + 1];
    const stage = $('#presentStage');
    stage.replaceChildren(el('div', { class: 'p-head', style: 'font: 4vh var(--en)' }, t('endOfDoc'), next ? el('div', { style: 'margin-top:3vh' }, el('a', { href: '#/doc/' + next, style: 'color:#f6d860', onclick: () => { setTimeout(() => presentOpen(0, false), 400); } }, t('nextDoc') + ': ' + tt(LIB.docs[next].title) + ' ›')) : null));
  }
  function presentClose() { $('#present').classList.remove('on'); if (document.fullscreenElement) document.exitFullscreen().catch(() => {}); }

  // ------------------------------------------------------------------ routing
  function go(h) { if (location.hash === h) route(); else location.hash = h; }
  async function route() {
    closeAll();
    if ($('#present').classList.contains('on') && !location.hash.startsWith('#/doc/')) presentClose();
    const h = location.hash || '#/';
    const [path, query] = h.slice(1).split('?');
    const p = path.split('/').filter(Boolean);
    try {
      await library();
      if (p[0] === 'n') await viewNode(p[1]);
      else if (p[0] === 'cat') await viewNode(p[1]);
      else if (p[0] === 'bible') await viewBible(p[1] ? decodeURIComponent(p[1]) : null);
      else if (p[0] === 'doc') { const m = /r=(\d+)/.exec(query || ''); await viewDoc(p[1], m ? +m[1] : null); }
      else if (p[0] === 'search') await viewSearch(decodeURIComponent(p[1] || ''));
      else if (p[0] === 'date') viewDate();
      else if (p[0] === 'occasion-readings') await viewOccasion();
      else if (p[0] === 'scripture-index') await viewScripture();
      else if (p[0] === 'index') await viewIndex();
      else { current = { id: null, rows: [], cols: [] }; await viewHome(); }
    } catch (e) {
      console.error(e);
      view.replaceChildren(el('div', { class: 'empty' }, 'Could not load: ' + e.message));
    }
  }

  function init() {
    loadSettings(); applyTheme();
    $('#btnBack').onclick = () => {
      if (location.hash.startsWith('#/doc/') && current.node) go('#/n/' + current.node.id);
      else if (history.length > 1) history.back(); else go('#/');
    };
    $('#barTitle').onclick = () => go('#/');
    $('#btnToc').onclick = () => openDrawer('toc');
    $('#btnBookmark').onclick = toggleBookmark;
    $('#btnSettings').onclick = () => { renderSettings(); openDrawer('settings'); };
    $('#btnSearch').onclick = () => go('#/search/');
    $('#btnPresent').onclick = () => {
      const first = [...view.querySelectorAll('.row')].find(r => r.getBoundingClientRect().bottom > 90);
      presentOpen(first ? +first.dataset.i : 0, true);
    };
    $('#scrim').onclick = closeAll;
    document.querySelectorAll('[data-close]').forEach(b => b.onclick = closeAll);
    $('#modal').onclick = e => { if (e.target.id === 'modal') closeAll(); };
    $('#pPrev').onclick = () => presentStep(-1);
    $('#pNext').onclick = () => presentStep(1);
    $('#pExit').onclick = presentClose;
    $('#pFull').onclick = () => { const pe = $('#present'); if (document.fullscreenElement) document.exitFullscreen().catch(() => {}); else if (pe.requestFullscreen) pe.requestFullscreen().catch(() => {}); };
    $('#presentStage').onclick = e => { if (e.target.closest('a')) return; (e.clientX < window.innerWidth / 3) ? presentStep(-1) : presentStep(1); };
    let tx = null;
    $('#present').addEventListener('touchstart', e => { tx = e.touches[0].clientX; }, { passive: true });
    $('#present').addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 50) presentStep(dx < 0 ? 1 : -1); tx = null; });
    document.addEventListener('keydown', e => {
      if ($('#present').classList.contains('on')) {
        if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); presentStep(1); }
        else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); presentStep(-1); }
        else if (e.key === 'Escape') presentClose();
      } else if (e.key === 'Escape') closeAll();
    });
    window.addEventListener('resize', () => { if ($('#present').classList.contains('on')) presentShow(); });
    let lastW = window.innerWidth;
    window.addEventListener('resize', () => { if (Math.abs(window.innerWidth - lastW) > 120 && current.id) { lastW = window.innerWidth; renderDoc(); } });
    window.addEventListener('hashchange', route);
    route();
    if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
  }
  init();
})();
