self.addEventListener("install", event => {
  event.waitUntil(
    caches.open("deal-cache").then(cache => {
      return cache.addAll([
        "./",
        "./index.html",
        "./app.js",
        "./manifest.json"
      ]);
    })
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(res => res || fetch(event.request))
  );
});
