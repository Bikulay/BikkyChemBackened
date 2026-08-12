const CACHE_NAME = "bikkychem-v1";

const APP_FILES = [
    "/",
    "/static/manifest.json",
    "/static/IMG_0898.png"
];


self.addEventListener("install", function(event) {

    event.waitUntil(

        caches.open(CACHE_NAME)
            .then(function(cache) {

                return cache.addAll(APP_FILES);

            })

    );

});


self.addEventListener("activate", function(event) {

    event.waitUntil(

        caches.keys()
            .then(function(cacheNames) {

                return Promise.all(

                    cacheNames
                        .filter(function(cacheName) {

                            return (
                                cacheName !== CACHE_NAME
                            );

                        })

                        .map(function(cacheName) {

                            return caches.delete(
                                cacheName
                            );

                        })

                );

            })

    );

});


self.addEventListener("fetch", function(event) {

    /*
     * Do not intercept API requests.
     *
     * Chemistry questions must always
     * reach the live Flask/OpenRouter backend.
     */

    if (
        event.request.url.includes("/ask") ||
        event.request.url.includes("/test-ai")
    ) {

        return;

    }


    event.respondWith(

        fetch(event.request)
            .catch(function() {

                return caches.match(
                    event.request
                );

            })

    );

});
