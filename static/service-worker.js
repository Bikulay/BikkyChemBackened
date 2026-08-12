const CACHE_NAME = "bikkychem-v2";


const APP_FILES = [

    "/",

    "/static/manifest.json",

    "/static/IMG_0898.png",

    "/static/Icons/Icon-192.png",

    "/static/Icons/Icon-512.png"

];



/* ============================================================
   INSTALL
   ============================================================ */

self.addEventListener(
    "install",
    function(event) {

        event.waitUntil(

            caches
                .open(CACHE_NAME)
                .then(
                    function(cache) {

                        return cache.addAll(
                            APP_FILES
                        );

                    }
                )

        );


        /*
         * Activate the new service worker
         * immediately.
         */

        self.skipWaiting();

    }
);



/* ============================================================
   ACTIVATE
   ============================================================ */

self.addEventListener(
    "activate",
    function(event) {

        event.waitUntil(

            caches
                .keys()
                .then(
                    function(cacheNames) {

                        return Promise.all(

                            cacheNames
                                .filter(
                                    function(cacheName) {

                                        return (
                                            cacheName !==
                                            CACHE_NAME
                                        );

                                    }
                                )

                                .map(
                                    function(cacheName) {

                                        return caches.delete(
                                            cacheName
                                        );

                                    }
                                )

                        );

                    }
                )

        );


        /*
         * Take control of open pages
         * immediately.
         */

        self.clients.claim();

    }
);



/* ============================================================
   FETCH
   ============================================================ */

self.addEventListener(
    "fetch",
    function(event) {


        const request =
            event.request;


        const url =
            new URL(
                request.url
            );



        /* ========================================================
           DO NOT CACHE POST REQUESTS
           ======================================================== */

        if (
            request.method !== "GET"
        ) {

            return;

        }



        /* ========================================================
           DO NOT INTERCEPT CHEMISTRY API REQUESTS
           ========================================================

           These requests must always reach Flask/OpenRouter.
        */

        if (
            url.pathname === "/ask" ||
            url.pathname === "/test-ai"
        ) {

            return;

        }



        /* ========================================================
           NORMAL GET REQUEST
           ======================================================== */

        event.respondWith(

            fetch(request)

                .then(
                    function(response) {

                        /*
                         * Return the live response.
                         *
                         * We do not cache every response,
                         * because dynamic Flask pages and
                         * API-related responses should remain
                         * live.
                         */

                        return response;

                    }
                )

                .catch(
                    function() {

                        /*
                         * If internet is unavailable,
                         * try the cached version.
                         */

                        return caches.match(
                            request
                        );

                    }
                )

        );

    }
);
