// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/// <reference lib="webworker" />

/*
  For more info about these packages visit https://developers.google.com/web/tools/workbox/modules
*/

import { clientsClaim } from 'workbox-core';

declare const self: ServiceWorkerGlobalScope;

clientsClaim();

// @ts-expect-error temporarily ignore this warning for debugging purposes
// eslint-disable-next-line no-underscore-dangle
const manifest = self.__WB_MANIFEST;

const staticAssets = (manifest as { url: string }[]).map(({ url }) => url);
const filesToCache = ['/assets/opencv/4.9.0/opencv.js', ...staticAssets];
const staticCacheName = 'assets-cache-v1';

// Upon SW installation, cache all files from `filesToCache`
self.addEventListener('install', (event: ExtendableEvent) => {
    event.waitUntil(
        caches.open(staticCacheName).then((cache) => {
            return cache.addAll(filesToCache);
        })
    );
});

self.addEventListener('activate', async (event: ExtendableEvent) => {
    event.waitUntil(
        caches.open(staticCacheName).then((cache) =>
            cache.keys().then((cacheKeys) =>
                Promise.all(
                    cacheKeys.map((request) => {
                        const url = new URL(request.url);

                        if (!filesToCache.includes(url.pathname)) {
                            return cache.delete(request);
                        }

                        return Promise.resolve(true);
                    })
                )
            )
        )
    );
});

// This allows the web app to trigger skipWaiting via
// registration.waiting.postMessage({type: 'SKIP_WAITING'})
self.addEventListener('message', (event: ExtendableMessageEvent) => {
    // Only accept messages from the same origin
    if (event.origin !== self.origin) {
        return;
    }

    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', (event: FetchEvent) => {
    if (isValidStaticFileRequest(event.request)) {
        event.respondWith(fromCacheOrFetch(event));
    }
});

const isValidStaticFileRequest = (request: Request) =>
    isValidHttpRequest(request) && /\.(js|css|svg|html|wasm|onnx|gif)$/.test(request.url);

const fromCacheOrFetch = (event: FetchEvent) =>
    caches.match(event.request, { ignoreSearch: true }).then((cacheResponse) => {
        return cacheResponse || fetchAndCatchWebWorker(event);
    });

const fetchAndCatchWebWorker = (event: FetchEvent) =>
    fetch(event.request).then((fetchResponse) => {
        return caches.open(staticCacheName).then((cache) => {
            cache.put(event.request, fetchResponse.clone());

            return fetchResponse;
        });
    });

const isValidHttpRequest = (request: Request) => {
    const { protocol } = new URL(request.url);

    return protocol.startsWith('http');
};
