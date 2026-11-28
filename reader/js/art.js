/* Original icon-style tile artwork (SVG), drawn for this app in a Coptic iconographic manner. */
(function () {
  const W = 100;
  const frame = (bg, inner) => `<svg viewBox="0 0 ${W} ${W}" xmlns="http://www.w3.org/2000/svg"><defs>${bg.defs || ''}</defs><rect width="100" height="100" fill="${bg.fill}"/>${inner}<rect x="1.5" y="1.5" width="97" height="97" rx="20" fill="none" stroke="rgba(0,0,0,.18)" stroke-width="3"/></svg>`;
  const grad = (id, stops, x2 = 0, y2 = 1) => `<linearGradient id="${id}" x1="0" y1="0" x2="${x2}" y2="${y2}">${stops.map(([o, c]) => `<stop offset="${o}" stop-color="${c}"/>`).join('')}</linearGradient>`;
  const rgrad = (id, stops) => `<radialGradient id="${id}" cx="50%" cy="40%" r="70%">${stops.map(([o, c]) => `<stop offset="${o}" stop-color="${c}"/>`).join('')}</radialGradient>`;
  const GOLD = { defs: rgrad('gd', [[0, '#f7e3a0'], [0.6, '#d9b158'], [1, '#a77a2a']]), fill: 'url(#gd)' };
  const copticCross = (cx, cy, s, fill, stroke) => {
    // slim equal-armed cross, each arm ending in a three-ball cluster (Coptic style)
    const h = s * 0.5, a = s * 0.07, r = s * 0.065, w = s * 0.13;
    let g = `<g fill="${fill}" stroke="${stroke || 'none'}" stroke-width="${stroke ? 0.8 : 0}">`;
    g += `<rect x="${cx - a}" y="${cy - h + r}" width="${a * 2}" height="${(h - r) * 2}"/><rect x="${cx - h + r}" y="${cy - a}" width="${(h - r) * 2}" height="${a * 2}"/>`;
    for (const [dx, dy] of [[0, -1], [0, 1], [-1, 0], [1, 0]]) {
      const ex = cx + dx * (h - r), ey = cy + dy * (h - r);
      const px = -dy, py = dx;                  // perpendicular
      g += `<path d="M${cx + dx * h * 0.55 + px * a} ${cy + dy * h * 0.55 + py * a} L${ex + px * w} ${ey + py * w} L${ex - px * w} ${ey - py * w} L${cx + dx * h * 0.55 - px * a} ${cy + dy * h * 0.55 - py * a}Z"/>`;
      g += `<circle cx="${ex + dx * r}" cy="${ey + dy * r}" r="${r}"/><circle cx="${ex + px * w}" cy="${ey + py * w}" r="${r}"/><circle cx="${ex - px * w}" cy="${ey - py * w}" r="${r}"/>`;
    }
    g += `<circle cx="${cx}" cy="${cy}" r="${a * 1.9}"/></g>`;
    return g;
  };


  // icon-style saint bust: gold ground, halo, beard, vestments with crosses, Coptic inscription
  function saint(o) {
    const halo = `<circle cx="50" cy="40" r="23" fill="#e9c66c" stroke="#8a5a1a" stroke-width="1.6"/><circle cx="50" cy="40" r="19.5" fill="none" stroke="#b98b35" stroke-width=".8"/>`;
    const robe = `<path d="M14 100 C16 76 30 66 50 64 C70 66 84 76 86 100 Z" fill="${o.robe}"/>`;
    const omo = `<path d="M30 70 L50 92 L70 70" fill="none" stroke="#f3eee2" stroke-width="7"/>${[[38, 80], [50, 91], [62, 80]].map(([x, y]) => `<path d="M${x - 2.4} ${y}h4.8M${x} ${y - 2.4}v4.8" stroke="#1d1d1d" stroke-width="1.6"/>`).join('')}`;
    const face = `<ellipse cx="50" cy="43" rx="10.5" ry="13" fill="#e2b98a" stroke="#7a4a22" stroke-width=".8"/>`;
    const eyes = `<path d="M44 41 q2 -1.6 4 0 M52 41 q2 -1.6 4 0" stroke="#3a2412" stroke-width="1.2" fill="none"/><circle cx="46" cy="41.6" r=".9" fill="#2a1a0c"/><circle cx="54" cy="41.6" r=".9" fill="#2a1a0c"/><path d="M50 42 v6 l-1.6 1" stroke="#7a4a22" stroke-width=".9" fill="none"/>`;
    const beardLen = o.beard === 'long' ? 74 : 64;
    const beard = `<path d="M39.5 46 C40 ${beardLen - 6} 46 ${beardLen} 50 ${beardLen} C54 ${beardLen} 60 ${beardLen - 6} 60.5 46 C57 52 54 54 50 54 C46 54 43 52 39.5 46 Z" fill="${o.beardColor}"/>`;
    let head = '';
    if (o.head === 'mitre') head = `<path d="M37 34 C37 18 63 18 63 34 Z" fill="#c9a13d" stroke="#6a4614" stroke-width="1"/><path d="M50 21v10M45.5 26h9" stroke="#7d1a1a" stroke-width="2"/><rect x="37" y="31" width="26" height="4" fill="#7d1a1a"/>`;
    if (o.head === 'hood') head = `<path d="M36 50 C33 28 40 20 50 20 C60 20 67 28 64 50 C62 40 59 33 50 33 C41 33 38 40 36 50 Z" fill="#1f1a17"/>`;
    if (o.head === 'turban') head = `<path d="M36 34 C35 14 65 14 64 34 C58 30 42 30 36 34 Z" fill="#f2efe6" stroke="#9a8f74" stroke-width="1"/><path d="M50 18v12M46 24h8" stroke="#7d1a1a" stroke-width="1.8"/>`;
    const book = o.book ? `<rect x="58" y="74" width="14" height="18" rx="1.5" fill="#7d1a1a" stroke="#d9b158" stroke-width="1.2"/><path d="M65 78v10M61 83h8" stroke="#d9b158" stroke-width="1.4"/>` : '';
    const cross = o.cross ? `<path d="M30 68v24M25 74h10" stroke="#d9b158" stroke-width="3" stroke-linecap="round"/>` : '';
    const name = `<text x="50" y="12" text-anchor="middle" font-family="CopticFont, 'Noto Sans Coptic', serif" font-size="9" fill="#5a1010" letter-spacing=".5">${o.name}</text>`;
    return frame(GOLD, `${halo}${robe}${omo}${head}${face}${beard}${eyes}${book}${cross}${name}`);
  }

  const A = {};
  A.basil = saint({ head: 'mitre', beard: 'long', beardColor: '#3b2a1c', robe: '#a52a1e', name: 'ⲂⲀⲤⲒⲖⲒⲞⲤ', book: true });
  A.gregory = saint({ head: 'hood', beard: 'long', beardColor: '#e9e4d6', robe: '#c4a35a', name: 'ⲄⲢⲎⲄⲞⲢⲒⲞⲤ', book: true });
  A.cyril = saint({ head: 'turban', beard: 'long', beardColor: '#5a4a3a', robe: '#8c1f1f', name: 'ⲔⲨⲢⲒⲖⲖⲞⲤ', cross: true });
  A.veneration = frame(GOLD, `<circle cx="50" cy="38" r="22" fill="#e9c66c" stroke="#8a5a1a" stroke-width="1.5"/><path d="M22 100 C22 60 34 40 50 40 C66 40 78 60 78 100Z" fill="#1e3a6e"/><path d="M28 100 C30 70 38 52 50 52 C62 52 70 70 72 100Z" fill="#8a1f1f"/><ellipse cx="50" cy="41" rx="9" ry="11" fill="#e2b98a"/><path d="M37 38 C38 26 62 26 63 38 C60 32 40 32 37 38Z" fill="#1e3a6e"/><circle cx="62" cy="62" r="8" fill="#e9c66c"/><ellipse cx="62" cy="63" rx="5" ry="6" fill="#e2b98a"/><path d="M56 70 C56 80 68 80 68 70Z" fill="#c9a13d"/><text x="50" y="12" text-anchor="middle" font-family="CopticFont, serif" font-size="8.5" fill="#5a1010">ⲘⲀⲢⲒⲀ</text>`);
  A.matins = frame({ defs: grad('sk', [[0, '#3b6ea8'], [0.55, '#f2a65a'], [0.75, '#f7d27a'], [1, '#5a3a1a']]), fill: 'url(#sk)' },
    `<circle cx="50" cy="74" r="16" fill="#ffe7a3" opacity=".9"/><path d="M0 84 Q50 70 100 84 V100 H0Z" fill="#2a1a10"/><path d="M50 18v62M36 34h28" stroke="#140c08" stroke-width="7" stroke-linecap="square"/>`);
  A.vespers = frame({ defs: rgrad('vs', [[0, '#6a4a2a'], [1, '#1a0f08']]), fill: 'url(#vs)' },
    `<path d="M30 10 Q40 30 46 46 M70 10 Q60 30 54 46 M50 8v38" stroke="#d9b158" stroke-width="1.6" fill="none"/>
     <path d="M36 50h28l-4 16H40Z" fill="#d9b158" stroke="#8a5a1a"/><path d="M38 66h24l-6 10H44Z" fill="#b98b35"/><circle cx="50" cy="48" r="3" fill="#f7e3a0"/>
     <path d="M52 44 C60 36 46 30 56 22 C64 16 56 10 62 4" stroke="#efe6d6" stroke-width="2.4" fill="none" opacity=".75"/><path d="M48 44 C42 38 52 32 44 24" stroke="#efe6d6" stroke-width="1.8" fill="none" opacity=".55"/>`);
  A.pascha = frame({ defs: rgrad('ps', [[0, '#6b1d2a'], [1, '#2a0810']]), fill: 'url(#ps)' },
    `${copticCross(50, 52, 46, '#d9b158', '#8a5a1a')}<circle cx="50" cy="30" r="15" fill="none" stroke="#5a3a1a" stroke-width="3.2"/>${Array.from({ length: 14 }, (_, i) => { const a = i / 14 * Math.PI * 2; return `<path d="M${50 + Math.cos(a) * 15} ${30 + Math.sin(a) * 15} l${Math.cos(a + .6) * 5} ${Math.sin(a + .6) * 5}" stroke="#3a2410" stroke-width="1.6"/>`; }).join('')}`);
  A.resurrection = frame({ defs: grad('rs', [[0, '#14244a'], [1, '#3b5a96']]), fill: 'url(#rs)' },
    `${Array.from({ length: 12 }, (_, i) => { const a = -Math.PI + i / 11 * Math.PI; return `<path d="M50 56 L${50 + Math.cos(a) * 60} ${56 + Math.sin(a) * 60}" stroke="#f7e3a0" stroke-width="2" opacity=".35"/>`; }).join('')}
     <path d="M18 100 V64 A32 32 0 0 1 82 64 V100Z" fill="#3a2e24"/><path d="M30 100 V66 A20 20 0 0 1 70 66 V100Z" fill="#fff4cf"/><path d="M38 84h24" stroke="#ffffff" stroke-width="5"/><path d="M50 22v26M42 30h16" stroke="#f7e3a0" stroke-width="3.5"/>`);
  A.lakkan = frame({ defs: grad('lk', [[0, '#c9dcef'], [1, '#5f86b5']]), fill: 'url(#lk)' },
    `<path d="M14 54 Q50 92 86 54 Z" fill="#c9a13d" stroke="#6a4614" stroke-width="1.5"/><ellipse cx="50" cy="54" rx="36" ry="7" fill="#7fb2df" stroke="#6a4614" stroke-width="1.5"/><path d="M40 70h20v8H40z" fill="#a77a2a"/>
     <path d="M62 14 C74 14 82 22 80 40 L74 40 C74 28 70 22 62 22Z" fill="#f4f1ea" stroke="#b9b0a0"/>${[[34, 26], [44, 34], [56, 30]].map(([x, y]) => `<path d="M${x} ${y} q3 6 0 8 q-3 -2 0 -8Z" fill="#2d6fb3"/>`).join('')}`);
  A.unction = frame({ defs: rgrad('un', [[0, '#3a2a14'], [1, '#100a05']]), fill: 'url(#un)' },
    `<path d="M16 66 Q50 92 84 66 Z" fill="#c9a13d" stroke="#6a4614" stroke-width="1.5"/><ellipse cx="50" cy="66" rx="34" ry="6" fill="#8a6a1a"/>
     ${[22, 31, 40, 50, 60, 69, 78].map((x, i) => `<path d="M${x} ${60 - (i % 2) * 3} q-4 -8 0 -14 q4 6 0 14Z" fill="#ffcf5a"/><path d="M${x} ${58 - (i % 2) * 3} q-2 -4 0 -7 q2 3 0 7Z" fill="#fff4cf"/>`).join('')}`);
  A.crowning = frame({ defs: rgrad('cr', [[0, '#a52a2a'], [1, '#4a0c0c']]), fill: 'url(#cr)' },
    [[30, 50], [70, 50]].map(([x, y]) => `<path d="M${x - 16} ${y + 12} L${x - 16} ${y - 6} L${x - 8} ${y + 2} L${x} ${y - 12} L${x + 8} ${y + 2} L${x + 16} ${y - 6} L${x + 16} ${y + 12}Z" fill="#e2bd5e" stroke="#7a5418" stroke-width="1.2"/><rect x="${x - 16}" y="${y + 10}" width="32" height="6" fill="#c9a13d" stroke="#7a5418"/><path d="M${x} ${y - 22}v8M${x - 4} ${y - 18}h8" stroke="#e2bd5e" stroke-width="2"/><circle cx="${x}" cy="${y + 13}" r="2" fill="#2d6fb3"/>`).join(''));
  A.funeral = frame({ defs: rgrad('fn', [[0, '#2b2620'], [1, '#08070a']]), fill: 'url(#fn)' },
    `<circle cx="50" cy="30" r="22" fill="#ffcf5a" opacity=".18"/><rect x="42" y="38" width="16" height="50" rx="2" fill="#efe6cf"/><path d="M50 14 q-8 12 0 22 q8 -10 0 -22Z" fill="#ffcf5a"/><path d="M50 22 q-3 6 0 12 q3 -6 0 -12Z" fill="#fff6d6"/><path d="M50 36v4" stroke="#222" stroke-width="1.5"/><path d="M34 88h32" stroke="#c9a13d" stroke-width="5"/>`);
  A.palm = frame(GOLD, `<path d="M30 92 C40 70 52 44 72 14" stroke="#3d6b2a" stroke-width="3" fill="none"/>${Array.from({ length: 10 }, (_, i) => { const t = i / 10; const x = 30 + t * 42 + (t * t * -6), y = 92 - t * 78; return `<path d="M${x} ${y} q-16 -2 -24 6" stroke="#4f8a34" stroke-width="3.2" fill="none"/><path d="M${x} ${y} q12 -8 22 -4" stroke="#4f8a34" stroke-width="3.2" fill="none"/>`; }).join('')}`);
  A.lazarus = frame({ defs: grad('lz', [[0, '#d9b158'], [1, '#8a6a2a']]), fill: 'url(#lz)' },
    `<path d="M16 100 V58 A34 34 0 0 1 84 58 V100Z" fill="#3a2e24"/><path d="M40 98 C38 70 42 50 50 46 C58 50 62 70 60 98Z" fill="#f4f1ea"/>${[56, 64, 72, 80, 88].map(y => `<path d="M40 ${y} L60 ${y - 4}" stroke="#b9b0a0" stroke-width="1.4"/>`).join('')}<circle cx="50" cy="42" r="7" fill="#f4f1ea" stroke="#b9b0a0"/>`);
  A.cross = frame({ defs: rgrad('cx', [[0, '#9a2020'], [1, '#3e0808']]), fill: 'url(#cx)' }, copticCross(50, 50, 60, '#e2bd5e', '#7a5418'));
  A.special = A.cross;
  A.feast = frame({ defs: rgrad('fe', [[0, '#7a3e18'], [1, '#2a1006']]), fill: 'url(#fe)' }, `${Array.from({ length: 16 }, (_, i) => { const a = i / 16 * Math.PI * 2; return `<path d="M50 50 L${50 + Math.cos(a) * 46} ${50 + Math.sin(a) * 46}" stroke="#f7e3a0" stroke-width="1.6" opacity=".35"/>`; }).join('')}${copticCross(50, 50, 52, '#f1d77a', '#7a5418')}`);
  A.fraction = frame({ defs: rgrad('fr', [[0, '#8a1f1f'], [1, '#3a0808']]), fill: 'url(#fr)' },
    `<circle cx="50" cy="50" r="34" fill="#e3b46e" stroke="#8a5a2a" stroke-width="2"/><circle cx="50" cy="50" r="29" fill="none" stroke="#a7743a" stroke-width="1.2"/>
     ${[-12, 0, 12].map(d => `<path d="M${50 + d} 26v48M26 ${50 + d}h48" stroke="#a7743a" stroke-width="1"/>`).join('')}<rect x="44" y="44" width="12" height="12" fill="#c98e48" stroke="#8a5a2a"/><path d="M50 46v8M46 50h8" stroke="#6a3a12" stroke-width="1.6"/>
     ${Array.from({ length: 12 }, (_, i) => { const a = i / 12 * Math.PI * 2; return `<circle cx="${50 + Math.cos(a) * 31.5}" cy="${50 + Math.sin(a) * 31.5}" r="1.2" fill="#8a5a2a"/>`; }).join('')}`);
  A.liturgies = frame({ defs: rgrad('lt', [[0, '#a52a1e'], [1, '#3e0c08']]), fill: 'url(#lt)' },
    `<path d="M32 18h36c0 22-8 34-18 36-10-2-18-14-18-36Z" fill="#e2bd5e" stroke="#7a5418" stroke-width="1.4"/><path d="M50 54v18M36 84c4-8 9-12 14-12s10 4 14 12Z" fill="#e2bd5e" stroke="#7a5418" stroke-width="1.4"/><path d="M50 24v18M43 31h14" stroke="#7d1a1a" stroke-width="3"/><circle cx="50" cy="16" r="9" fill="#e3b46e" stroke="#8a5a2a" opacity=".0"/>`);
  A.liturgy = A.liturgies; A.communion = frame({ defs: rgrad('cm', [[0, '#7a5a2a'], [1, '#2a1a08']]), fill: 'url(#cm)' },
    `<path d="M24 30h32c0 20-7 30-16 32-9-2-16-12-16-32Z" fill="#e2bd5e" stroke="#7a5418"/><path d="M40 62v14M28 86c3-6 7-10 12-10s9 4 12 10Z" fill="#e2bd5e" stroke="#7a5418"/><circle cx="68" cy="58" r="17" fill="#e3b46e" stroke="#8a5a2a" stroke-width="1.5"/><path d="M68 47v22M57 58h22" stroke="#a7743a" stroke-width="1.4"/><path d="M40 34v14M34 40h12" stroke="#7d1a1a" stroke-width="2.4"/>`);
  A.agpeya = frame({ defs: rgrad('ag', [[0, '#4a3420'], [1, '#120a05']]), fill: 'url(#ag)' },
    `${Array.from({ length: 15 }, (_, i) => { const a = Math.PI * (0.15 + i / 14 * 1.7); return `<circle cx="${50 + Math.cos(a) * 28}" cy="${44 - Math.sin(a) * 26}" r="4" fill="#d7c2a0" stroke="#6a5432"/>`; }).join('')}<path d="M50 70v18M43 77h14" stroke="#d7c2a0" stroke-width="4" stroke-linecap="round"/><path d="M28 54 Q50 76 72 54" stroke="#d7c2a0" stroke-width="1.5" fill="none"/>`);
  A.psalmody = frame(GOLD, `<path d="M28 92 C22 62 26 30 46 10 C52 24 66 30 78 30 C74 50 74 72 80 92Z" fill="#7d1a1a" stroke="#4a0c0c" stroke-width="1.6"/>${[38, 47, 56, 65, 72].map((x, i) => `<path d="M${x} ${22 + i * 2} V${88}" stroke="#f7e3a0" stroke-width="1.6"/>`).join('')}<path d="M28 92h52" stroke="#4a0c0c" stroke-width="4"/>`);
  A.doxology = frame({ defs: grad('dx', [[0, '#1e3a6e'], [1, '#0a1a38']]), fill: 'url(#dx)' },
    `${Array.from({ length: 8 }, (_, i) => { const a = i / 8 * Math.PI * 2; return `<path d="M50 50 L${50 + Math.cos(a) * 34} ${50 + Math.sin(a) * 34} L${50 + Math.cos(a + 0.39) * 14} ${50 + Math.sin(a + 0.39) * 14}Z" fill="#e2bd5e"/>`; }).join('')}<circle cx="50" cy="50" r="9" fill="#1e3a6e" stroke="#e2bd5e" stroke-width="2"/>`);
  A.cymbals = frame({ defs: rgrad('cy', [[0, '#9a2525'], [1, '#3e0a0a']]), fill: 'url(#cy)' },
    `<ellipse cx="34" cy="44" rx="20" ry="8" fill="#e2bd5e" stroke="#7a5418" transform="rotate(-25 34 44)"/><ellipse cx="66" cy="44" rx="20" ry="8" fill="#e2bd5e" stroke="#7a5418" transform="rotate(25 66 44)"/><circle cx="34" cy="44" r="3" fill="#7a5418"/><circle cx="66" cy="44" r="3" fill="#7a5418"/><path d="M50 62 L36 86 H64 Z" fill="none" stroke="#e2bd5e" stroke-width="3"/><path d="M47 20 l3 6 3-6" stroke="#f7e3a0" stroke-width="2" fill="none"/>`);
  A.melodies = A.cymbals;
  A.bible = frame({ defs: grad('bb', [[0, '#6b7078'], [1, '#2a2f36']]), fill: 'url(#bb)' },
    `<path d="M50 30c-10-6-24-8-36-6v52c12-2 26 0 36 6 10-6 24-8 36-6V24c-12-2-26 0-36 6z" fill="#f4efe0" stroke="#3a2e24" stroke-width="1.4"/><path d="M50 30v52" stroke="#3a2e24" stroke-width="1.4"/>${[38, 46, 54, 62].map(y => `<path d="M20 ${y}h22M58 ${y}h22" stroke="#b9ae96" stroke-width="1.2"/>`).join('')}${copticCross(50, 14, 12, '#7d1a1a')}`);
  A.readings = frame({ defs: grad('rd', [[0, '#a58a5a'], [1, '#4a3a22']]), fill: 'url(#rd)' },
    `<path d="M26 18h48v62H26z" fill="#f2e6c6" stroke="#5a4426" stroke-width="1.4"/><path d="M26 18c4 6 4 10 0 14M74 18c-4 6-4 10 0 14" stroke="#5a4426" fill="none"/><rect x="34" y="24" width="32" height="8" fill="#7d1a1a"/>${[38, 44, 50, 56, 62, 68].map(y => `<path d="M32 ${y}h36" stroke="#9a8460" stroke-width="1.4"/>`).join('')}<path d="M44 80 L40 94 M56 80 L60 94" stroke="#5a4426" stroke-width="3"/>`);
  A.today = frame({ defs: grad('td', [[0, '#f6d38a'], [1, '#d9792a']]), fill: 'url(#td)' },
    `<circle cx="50" cy="50" r="18" fill="#fff1c4"/>${Array.from({ length: 12 }, (_, i) => { const a = i / 12 * Math.PI * 2; return `<path d="M${50 + Math.cos(a) * 24} ${50 + Math.sin(a) * 24} L${50 + Math.cos(a) * 34} ${50 + Math.sin(a) * 34}" stroke="#fff1c4" stroke-width="3" stroke-linecap="round"/>`; }).join('')}${copticCross(50, 50, 18, '#9a3a14')}`);
  A.index = frame({ defs: grad('ix', [[0, '#33465f'], [1, '#142034']]), fill: 'url(#ix)' },
    [[22, '#7d1a1a'], [44, '#2b3d5c'], [66, '#5a4426']].map(([y, c]) => `<rect x="18" y="${y}" width="64" height="16" rx="2" fill="${c}" stroke="#d9b158" stroke-width="1.4"/><path d="M26 ${y + 8}h30" stroke="#d9b158" stroke-width="1.6"/>`).join('') + `<path d="M70 22v20l4-4 4 4V22" fill="#c0392b"/>`);
  A.clergy = frame({ defs: rgrad('cl', [[0, '#5a4a2a'], [1, '#1a1208']]), fill: 'url(#cl)' },
    `<path d="M44 60 C40 70 40 84 46 94 H58 C62 84 62 70 58 60Z" fill="#e2b98a"/>${copticCross(51, 34, 40, '#e2bd5e', '#7a5418')}<path d="M51 52v10" stroke="#e2bd5e" stroke-width="4"/>`);

  // baptismal font with the descending dove
  A.baptism = frame({ defs: grad('bp', [[0, '#e9f2fb'], [1, '#6f9fd0']]), fill: 'url(#bp)' },
    `<circle cx="50" cy="26" r="14" fill="#fff6d6" opacity=".7"/><path d="M50 20 q-10 -6 -18 2 q8 0 12 4 q-6 4 -4 10 q4 -6 10 -6 q6 0 10 6 q2 -6 -4 -10 q4 -4 12 -4 q-8 -8 -18 -2Z" fill="#ffffff" stroke="#9aa9b8" stroke-width=".8"/>
     ${[0, 1, 2].map(i => `<path d="M${44 + i * 6} 40 v8" stroke="#ffffff" stroke-width="1.6" opacity=".8"/>`).join('')}
     <path d="M20 58 h60 l-8 22 h-44z" fill="#c9a13d" stroke="#6a4614" stroke-width="1.5"/><ellipse cx="50" cy="58" rx="30" ry="6" fill="#7fb2df" stroke="#6a4614" stroke-width="1.5"/><rect x="40" y="80" width="20" height="10" fill="#a77a2a" stroke="#6a4614"/>${copticCross(50, 69, 16, '#7a5418')}`);
  // Pentecost kneeling prayers: tongues of fire over a kneeling figure
  A.prostration = frame({ defs: rgrad('ps', [[0, '#a33a1e'], [1, '#3a0e06']]), fill: 'url(#ps)' },
    `${[26, 38, 50, 62, 74].map((x, i) => `<path d="M${x} ${30 - (i % 2) * 6} q-5 -9 0 -16 q5 7 0 16Z" fill="#ffb03a"/><path d="M${x} ${28 - (i % 2) * 6} q-2 -5 0 -8 q2 4 0 8Z" fill="#fff1c4"/>`).join('')}
     <circle cx="40" cy="58" r="6" fill="#e9d3b0"/><path d="M34 64 q10 -2 16 8 l12 10 h-30 q-4 -10 2 -18Z" fill="#e2bd5e" stroke="#7a5418"/><path d="M50 70 l14 -6" stroke="#e2bd5e" stroke-width="3" stroke-linecap="round"/><path d="M22 86h56" stroke="#e2bd5e" stroke-width="3"/>`);
  // the Apostles: St Peter's keys and St Paul's sword
  A.apostles = frame(GOLD,
    `<g transform="rotate(-35 50 52)"><rect x="47" y="20" width="6" height="52" fill="#7a5418"/><circle cx="50" cy="18" r="8" fill="none" stroke="#7a5418" stroke-width="4"/><rect x="53" y="60" width="10" height="4" fill="#7a5418"/><rect x="53" y="67" width="7" height="4" fill="#7a5418"/></g>
     <g transform="rotate(35 50 52)"><path d="M47 14 h6 v58 l-3 8 l-3 -8z" fill="#e9ecef" stroke="#5b6470" stroke-width="1"/><rect x="38" y="68" width="24" height="4" fill="#8a2a1a"/><rect x="47.5" y="72" width="5" height="12" fill="#8a2a1a"/></g>`);
  A.default = A.cross;
  window.TILE_ART = A;
})();
