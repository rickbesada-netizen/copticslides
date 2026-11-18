/* Coptic calendar: Coptic dates, Orthodox (Coptic) Easter, Holy Week mapping. */
(function (root) {
  'use strict';
  const EPOCH = 1825030; // JDN of 1 Thout, 1 A.M.
  const MONTHS = {
    en: ['Thout', 'Paopi', 'Hathor', 'Koiak', 'Tobi', 'Meshir', 'Paremhat', 'Parmouti', 'Pashons', 'Paoni', 'Epip', 'Mesori', 'Nesi'],
    ar: ['توت', 'بابه', 'هاتور', 'كيهك', 'طوبه', 'أمشير', 'برمهات', 'برموده', 'بشنس', 'بؤونه', 'أبيب', 'مسرى', 'النسيء'],
    cop: ['Ⲑⲱⲟⲩⲧ', 'Ⲡⲁⲟⲡⲓ', 'Ⲁⲑⲱⲣ', 'Ⲭⲟⲓⲁⲕ', 'Ⲧⲱⲃⲓ', 'Ⲙⲉϣⲓⲣ', 'Ⲡⲁⲣⲉⲙϩⲁⲧ', 'Ⲫⲁⲣⲙⲟⲩⲑⲓ', 'Ⲡⲁϣⲁⲛⲥ', 'Ⲡⲁⲱⲛⲓ', 'Ⲉⲡⲏⲡ', 'Ⲙⲉⲥⲱⲣⲓ', 'Ⲡⲓⲕⲟⲩϫⲓ ⲛ̀ⲁ̀ⲃⲟⲧ']
  };
  function gregToJDN(y, m, d) {
    const a = Math.floor((14 - m) / 12), yy = y + 4800 - a, mm = m + 12 * a - 3;
    return d + Math.floor((153 * mm + 2) / 5) + 365 * yy + Math.floor(yy / 4) - Math.floor(yy / 100) + Math.floor(yy / 400) - 32045;
  }
  function jdnToGreg(j) {
    const a = j + 32044, b = Math.floor((4 * a + 3) / 146097), c = a - Math.floor(146097 * b / 4);
    const d = Math.floor((4 * c + 3) / 1461), e = c - Math.floor(1461 * d / 4), m = Math.floor((5 * e + 2) / 153);
    return { y: 100 * b + d - 4800 + Math.floor(m / 10), m: m + 3 - 12 * Math.floor(m / 10), d: e - Math.floor((153 * m + 2) / 5) + 1 };
  }
  function copticToJDN(y, m, d) { return EPOCH - 1 + 365 * (y - 1) + Math.floor(y / 4) + 30 * (m - 1) + d; }
  function jdnToCoptic(j) {
    const y = Math.floor((4 * (j - EPOCH) + 1463) / 1461);
    const m = 1 + Math.floor((j - copticToJDN(y, 1, 1)) / 30);
    const d = j + 1 - copticToJDN(y, m, 1);
    return { y, m, d };
  }
  function julianToJDN(y, m, d) {
    const a = Math.floor((14 - m) / 12), yy = y + 4800 - a, mm = m + 12 * a - 3;
    return d + Math.floor((153 * mm + 2) / 5) + 365 * yy + Math.floor(yy / 4) - 32083;
  }
  // Orthodox Easter (Julian computus) as JDN
  function easterJDN(y) {
    const a = y % 4, b = y % 7, c = y % 19;
    const d = (19 * c + 15) % 30, e = (2 * a + 4 * b - d + 34) % 7;
    const month = Math.floor((d + e + 114) / 31), day = ((d + e + 114) % 31) + 1;
    return julianToJDN(y, month, day);
  }
  function todayJDN(date) {
    const t = date || new Date();
    return gregToJDN(t.getFullYear(), t.getMonth() + 1, t.getDate());
  }
  // Days relative to Easter -> Holy Week key
  const HOLY = {
    '-9': 'last-friday', '-8': 'lazarus', '-7': 'palm', '-6': 'monday', '-5': 'tuesday', '-4': 'wednesday',
    '-3': 'thursday', '-2': 'friday', '-1': 'saturday', '0': 'easter'
  };
  function season(j) {
    const g = jdnToGreg(j);
    let E = easterJDN(g.y);
    const diff = j - E;
    const out = { easter: jdnToGreg(E), diff };
    if (HOLY[diff] !== undefined) out.holy = HOLY[diff];
    if (diff >= -55 && diff < -9) out.season = 'lent';
    else if (diff >= -9 && diff < 0) out.season = 'pascha';
    else if (diff >= 0 && diff < 50) out.season = 'pentecost50';
    else out.season = 'ordinary';
    // Nativity fast / Nativity (29 Koiak), Theophany (11 Tobi)
    const c = jdnToCoptic(j);
    if ((c.m === 4 && c.d === 29) || (c.m === 4 && c.d === 28 && (c.y + 1) % 4 === 0)) out.feast = 'nativity';
    if (c.m === 5 && c.d === 11) out.feast = 'theophany';
    return out;
  }
  function formatCoptic(j, lang) {
    const c = jdnToCoptic(j);
    const names = MONTHS[lang] || MONTHS.en;
    if (lang === 'ar') return `${c.d} ${names[c.m - 1]} ${c.y} ش`;
    return `${c.d} ${names[c.m - 1]} ${c.y} A.M.`;
  }

  // ---- Church seasons and occasions --------------------------------------
  const ORD = n => n + (n % 10 === 1 && n % 100 !== 11 ? 'st' : n % 10 === 2 && n % 100 !== 12 ? 'nd' : n % 10 === 3 && n % 100 !== 13 ? 'rd' : 'th');
  const AR_ORD = ['', 'الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس', 'السابع', 'الثامن'];
  function copticYearOf(j) { return jdnToCoptic(j).y; }
  // occasions for the Coptic year containing jdn j
  function occasions(j) {
    const cy = copticYearOf(j);
    const C = (m, d) => copticToJDN(cy, m, d);
    const g = jdnToGreg(C(8, 1)); // Easter falls in the Gregorian year of Paremhat
    const E = easterJDN(g.y);
    const list = [
      ['nayrouz', 'Coptic New Year (Nayrouz)', 'عيد النيروز', C(1, 1)],
      ['cross', 'Feast of the Cross', 'عيد الصليب', C(1, 17)],
      ['nativity-fast', 'Beginning of the Nativity Fast', 'بدء صوم الميلاد', C(3, 16)],
      ['kiahk', 'Month of Kiahk', 'شهر كيهك', C(4, 1)],
      ['nativity-paramoun', 'Nativity Paramoun', 'برامون الميلاد', C(4, 28)],
      ['nativity', 'Feast of the Nativity', 'عيد الميلاد المجيد', C(4, 29)],
      ['circumcision', 'Circumcision of the Lord', 'عيد الختان', C(5, 6)],
      ['theophany-paramoun', 'Theophany Paramoun', 'برامون الغطاس', C(5, 10)],
      ['theophany', 'Feast of Theophany', 'عيد الغطاس المجيد', C(5, 11)],
      ['cana', 'Wedding at Cana of Galilee', 'عرس قانا الجليل', C(5, 13)],
      ['jonah', 'Jonah’s Fast', 'صوم يونان', E - 69],
      ['jonah-passover', 'Jonah’s Passover', 'فصح يونان', E - 66],
      ['presentation', 'Presentation of the Lord in the Temple', 'دخول المسيح الهيكل', C(6, 8)],
      ['lent', 'Beginning of Great Lent', 'بدء الصوم الكبير', E - 55],
      ['last-friday', 'Last Friday of Great Lent', 'جمعة ختام الصوم', E - 9],
      ['lazarus', 'Lazarus Saturday', 'سبت لعازر', E - 8],
      ['palm', 'Palm Sunday', 'أحد الشعانين', E - 7],
      ['monday', 'Monday of the Holy Pascha', 'اثنين البصخة', E - 6],
      ['tuesday', 'Tuesday of the Holy Pascha', 'ثلاثاء البصخة', E - 5],
      ['wednesday', 'Wednesday of the Holy Pascha', 'أربعاء البصخة', E - 4],
      ['thursday', 'Covenant Thursday', 'خميس العهد', E - 3],
      ['friday', 'Good Friday', 'الجمعة العظيمة', E - 2],
      ['saturday', 'Bright Saturday', 'سبت الفرح', E - 1],
      ['easter', 'Feast of the Resurrection', 'عيد القيامة المجيد', E],
      ['thomas', 'Thomas Sunday', 'أحد توما', E + 7],
      ['ascension', 'Feast of the Ascension', 'عيد الصعود', E + 39],
      ['pentecost', 'Feast of Pentecost', 'عيد العنصرة', E + 49],
      ['apostles-fast', 'Apostles’ Fast', 'صوم الرسل', E + 50],
      ['apostles', 'Feast of the Apostles', 'عيد الرسل', C(11, 5)],
      ['mary-fast', 'St Mary’s Fast', 'صوم السيدة العذراء', C(12, 1)],
      ['transfiguration', 'Feast of the Transfiguration', 'عيد التجلي', C(12, 13)],
      ['assumption', 'Assumption of St Mary', 'عيد صعود جسد العذراء', C(12, 16)],
    ];
    return list.map(([key, en, ar, jdn]) => ({ key, en, ar, jdn })).sort((a, b) => a.jdn - b.jdn);
  }
  function seasonInfo(j) {
    const c = jdnToCoptic(j);
    const g = jdnToGreg(j);
    let E = easterJDN(g.y);
    if (j - E > 200) E = easterJDN(g.y + 1);
    const d = j - E;
    const holyNames = { '-9': ['Last Friday of Great Lent', 'جمعة ختام الصوم'], '-8': ['Lazarus Saturday', 'سبت لعازر'], '-7': ['Palm Sunday', 'أحد الشعانين'],
      '-6': ['Monday of the Holy Pascha', 'اثنين البصخة المقدسة'], '-5': ['Tuesday of the Holy Pascha', 'ثلاثاء البصخة المقدسة'],
      '-4': ['Wednesday of the Holy Pascha', 'أربعاء البصخة المقدسة'], '-3': ['Covenant Thursday', 'خميس العهد'], '-2': ['Good Friday', 'الجمعة العظيمة'],
      '-1': ['Bright Saturday', 'سبت الفرح'], '0': ['Feast of the Resurrection', 'عيد القيامة المجيد'], '39': ['Feast of the Ascension', 'عيد الصعود'],
      '49': ['Feast of Pentecost', 'عيد العنصرة'] };
    if (holyNames[d]) return { en: holyNames[d][0], ar: holyNames[d][1], key: 'holy' };
    if (d > 0 && d < 50) { const w = Math.floor(d / 7) + 1; return { en: `${ORD(w)} Week of the Holy Fifty Days`, ar: `الأسبوع ${AR_ORD[w] || w} من الخماسين`, key: 'pentecost50' }; }
    if (d >= -55 && d < -9) { const w = Math.floor((d + 55) / 7) + 1; return { en: `${ORD(w)} Week of Great Lent`, ar: `الأسبوع ${AR_ORD[w] || w} من الصوم الكبير`, key: 'lent' }; }
    if (d >= -69 && d <= -66) return { en: 'Jonah’s Fast', ar: 'صوم يونان', key: 'jonah' };
    const occ = occasions(j).find(o => o.jdn === j && !['kiahk', 'nativity-fast', 'lent', 'apostles-fast', 'mary-fast'].includes(o.key));
    if (occ) return { en: occ.en, ar: occ.ar, key: occ.key };
    const apEnd = copticToJDN(jdnToCoptic(E).y, 11, 5);
    if (d >= 50 && j < apEnd) return { en: 'Apostles’ Fast', ar: 'صوم الرسل', key: 'apostles-fast' };
    if (c.m === 12 && c.d <= 15) return { en: 'St Mary’s Fast', ar: 'صوم السيدة العذراء', key: 'mary-fast' };
    if (c.m === 4) return { en: 'Month of Kiahk', ar: 'شهر كيهك', key: 'kiahk' };
    if ((c.m === 3 && c.d >= 16)) return { en: 'Nativity Fast', ar: 'صوم الميلاد', key: 'nativity-fast' };
    if (c.m === 1 && c.d < 17) return { en: 'Season of the Nayrouz', ar: 'أيام النيروز', key: 'nayrouz' };
    if (c.m === 1 && c.d <= 19) return { en: 'Feast of the Cross', ar: 'عيد الصليب', key: 'cross' };
    if (c.m === 5 && c.d >= 11 && c.d <= 13) return { en: 'Theophany season', ar: 'أيام الغطاس', key: 'theophany' };
    const wd = new Date(g.y, g.m - 1, g.d).getDay();
    return wd === 0 ? { en: 'Annual Sunday', ar: 'أحد سنوي', key: 'annual' } : { en: 'Annual Weekday', ar: 'يوم سنوي', key: 'annual' };
  }
  root.CopticCal = { gregToJDN, jdnToGreg, jdnToCoptic, copticToJDN, easterJDN, todayJDN, season, formatCoptic, MONTHS, occasions, seasonInfo };
  if (typeof module !== 'undefined') module.exports = root.CopticCal;
})(typeof window !== 'undefined' ? window : globalThis);
