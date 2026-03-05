const SW_VERSION = (() => {
    try {
        const url = new URL(self.location.href);
        return url.searchParams.get('v') || 'dev';
    } catch (_) {
        return 'dev';
    }
})();

const CACHE_NAME = 'wine-list-v' + SW_VERSION;
const ASSETS = [
    './',
    './index.html',
    './wine_trainer.html',
    './wine_catalog.html',
    './wine_builder.html',
    './data/loader.js',
    './data/categories/wines-list.json'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    if (!event.request.url.startsWith('http')) return;

    event.respondWith(
        fetch(event.request)
            .then(response => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                return response;
            })
            .catch(() => {
                return caches.match(event.request)
                    .then(cached => cached || caches.match('./index.html'));
            })
    );
});
