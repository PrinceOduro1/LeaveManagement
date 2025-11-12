var staticCacheName = 'leave-system-v1';

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(staticCacheName).then(function(cache) {
      return cache.addAll([
        '/',
        '/static/css/bootstrap.min.css',
        '/static/js/bootstrap.bundle.min.js',
        '/static/images/logo1.png',
      ]);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
