/* Offline cache: app shell precached, data and images cached on first use */
const V = 'lr-v5';
const SHELL = ['./', 'index.html', 'css/app.css', 'js/app.js', 'js/i18n.js', 'js/translit.js', 'js/calendar.js', 'js/icons.js', 'js/art.js', 'manifest.webmanifest',
  'fonts/coptic.woff2', 'fonts/amiri-400.woff2', 'fonts/amiri-700.woff2', 'fonts/garamond-400.woff2', 'fonts/garamond-600.woff2', 'fonts/garamond-400i.woff2',
  'data/library.json', 'icons/icon-192.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  const isShell = /\.(html|js|css|webmanifest)$/.test(u.pathname) || u.pathname.endsWith('/') || u.pathname.endsWith('library.json');
  if (isShell) {
    // network first so updates arrive, cache fallback offline
    e.respondWith(fetch(e.request).then(r => { const cp = r.clone(); caches.open(V).then(c => c.put(e.request, cp)); return r; }).catch(() => caches.match(e.request).then(r => r || caches.match('index.html'))));
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => { if (res.ok) { const cp = res.clone(); caches.open(V).then(c => c.put(e.request, cp)); } return res; })));
  }
});
