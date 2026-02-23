const CACHE_NAME = 'food-list-v3';
const ASSETS = [
    './',
    './index.html',
    './food_trainer.html',
    './mobile_food.html',
    './food_builder.html',
    './data/loader.js',
    './data/categories/scotts.js',
    './data/categories/scotts_previous.js'
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
    // Only handle http/https requests (skip chrome-extension:// etc.)
    if (!event.request.url.startsWith('http')) return;

    event.respondWith(
        fetch(event.request)
            .then(response => {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseClone);
                });
                return response;
            })
            .catch(() => {
                return caches.match(event.request)
                    .then(cached => cached || caches.match('./index.html'));
            })
    );
});
