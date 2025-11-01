// Service Worker for Enterprise CIA - Intelligent Caching Strategy
const CACHE_NAME = "enterprise-cia-v1";
const STATIC_CACHE = "static-assets-v1";
const API_CACHE = "api-responses-v1";
const RUNTIME_CACHE = "runtime-v1";

// Cache strategies configuration
const CACHE_STRATEGIES = {
  // Static assets - Cache First with long TTL
  static: {
    cacheName: STATIC_CACHE,
    strategy: "CacheFirst",
    maxAge: 365 * 24 * 60 * 60 * 1000, // 1 year
    maxEntries: 100,
  },
  // API responses - Network First with fallback
  api: {
    cacheName: API_CACHE,
    strategy: "NetworkFirst",
    maxAge: 5 * 60 * 1000, // 5 minutes
    maxEntries: 50,
  },
  // Runtime resources - Stale While Revalidate
  runtime: {
    cacheName: RUNTIME_CACHE,
    strategy: "StaleWhileRevalidate",
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    maxEntries: 30,
  },
};

// Assets to precache on install
const PRECACHE_ASSETS = [
  "/",
  "/dashboard",
  "/_next/static/css/",
  "/favicon.ico",
];

// Install event - precache critical assets
self.addEventListener("install", (event) => {
  console.log("[SW] Installing service worker...");

  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);

        // Precache critical assets
        await cache.addAll(PRECACHE_ASSETS.filter((url) => !url.endsWith("/")));

        console.log("[SW] Precached critical assets");

        // Skip waiting to activate immediately
        self.skipWaiting();
      } catch (error) {
        console.error("[SW] Precaching failed:", error);
      }
    })()
  );
});

// Activate event - clean up old caches
self.addEventListener("activate", (event) => {
  console.log("[SW] Activating service worker...");

  event.waitUntil(
    (async () => {
      try {
        // Clean up old caches
        const cacheNames = await caches.keys();
        const oldCaches = cacheNames.filter(
          (name) =>
            name !== CACHE_NAME &&
            name !== STATIC_CACHE &&
            name !== API_CACHE &&
            name !== RUNTIME_CACHE
        );

        await Promise.all(
          oldCaches.map((cacheName) => {
            console.log("[SW] Deleting old cache:", cacheName);
            return caches.delete(cacheName);
          })
        );

        // Take control of all clients
        await self.clients.claim();

        console.log("[SW] Service worker activated");
      } catch (error) {
        console.error("[SW] Activation failed:", error);
      }
    })()
  );
});

// Fetch event - implement caching strategies
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== "GET") {
    return;
  }

  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith("http")) {
    return;
  }

  event.respondWith(handleRequest(request));
});

// Main request handler with intelligent routing
async function handleRequest(request) {
  const url = new URL(request.url);

  try {
    // Route to appropriate cache strategy
    if (isStaticAsset(url)) {
      return await cacheFirst(request, CACHE_STRATEGIES.static);
    } else if (isAPIRequest(url)) {
      return await networkFirst(request, CACHE_STRATEGIES.api);
    } else if (isRuntimeResource(url)) {
      return await staleWhileRevalidate(request, CACHE_STRATEGIES.runtime);
    } else {
      // Default to network with cache fallback
      return await networkWithCacheFallback(request);
    }
  } catch (error) {
    console.error("[SW] Request handling failed:", error);
    return await networkWithCacheFallback(request);
  }
}

// Cache First strategy - for static assets
async function cacheFirst(request, config) {
  const cache = await caches.open(config.cacheName);
  const cachedResponse = await cache.match(request);

  if (cachedResponse && !isExpired(cachedResponse, config.maxAge)) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Clone response before caching
      const responseToCache = networkResponse.clone();
      await cache.put(request, responseToCache);
      await cleanupCache(config.cacheName, config.maxEntries);
    }

    return networkResponse;
  } catch (error) {
    // Return stale cache if network fails
    if (cachedResponse) {
      console.log("[SW] Returning stale cache due to network error");
      return cachedResponse;
    }
    throw error;
  }
}

// Network First strategy - for API requests
async function networkFirst(request, config) {
  const cache = await caches.open(config.cacheName);

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful responses
      const responseToCache = networkResponse.clone();
      await cache.put(request, responseToCache);
      await cleanupCache(config.cacheName, config.maxEntries);
    }

    return networkResponse;
  } catch (error) {
    // Fallback to cache
    const cachedResponse = await cache.match(request);

    if (cachedResponse && !isExpired(cachedResponse, config.maxAge)) {
      console.log("[SW] Returning cached API response due to network error");
      return cachedResponse;
    }

    throw error;
  }
}

// Stale While Revalidate strategy - for runtime resources
async function staleWhileRevalidate(request, config) {
  const cache = await caches.open(config.cacheName);
  const cachedResponse = await cache.match(request);

  // Always try to fetch in background
  const fetchPromise = fetch(request)
    .then(async (networkResponse) => {
      if (networkResponse.ok) {
        const responseToCache = networkResponse.clone();
        await cache.put(request, responseToCache);
        await cleanupCache(config.cacheName, config.maxEntries);
      }
      return networkResponse;
    })
    .catch((error) => {
      console.log("[SW] Background fetch failed:", error);
      return null;
    });

  // Return cache immediately if available and not expired
  if (cachedResponse && !isExpired(cachedResponse, config.maxAge)) {
    // Don't await the fetch promise - let it update cache in background
    fetchPromise;
    return cachedResponse;
  }

  // Wait for network if no cache or expired
  try {
    return await fetchPromise;
  } catch (error) {
    // Return stale cache as last resort
    if (cachedResponse) {
      console.log("[SW] Returning stale cache as last resort");
      return cachedResponse;
    }
    throw error;
  }
}

// Network with cache fallback - default strategy
async function networkWithCacheFallback(request) {
  try {
    const networkResponse = await fetch(request);

    // Cache successful responses in runtime cache
    if (networkResponse.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      const responseToCache = networkResponse.clone();
      await cache.put(request, responseToCache);
    }

    return networkResponse;
  } catch (error) {
    // Try all caches as fallback
    const cacheNames = [RUNTIME_CACHE, STATIC_CACHE, API_CACHE, CACHE_NAME];

    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const cachedResponse = await cache.match(request);

      if (cachedResponse) {
        console.log(`[SW] Returning fallback from ${cacheName}`);
        return cachedResponse;
      }
    }

    throw error;
  }
}

// Helper functions
function isStaticAsset(url) {
  return (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/static/") ||
    url.pathname.match(
      /\.(js|css|png|jpg|jpeg|gif|webp|avif|svg|ico|woff|woff2|ttf)$/
    ) ||
    url.pathname === "/favicon.ico"
  );
}

function isAPIRequest(url) {
  return (
    url.pathname.startsWith("/api/") || url.hostname !== self.location.hostname
  );
}

function isRuntimeResource(url) {
  return (
    url.pathname.startsWith("/_next/") ||
    url.pathname === "/" ||
    url.pathname.startsWith("/dashboard") ||
    url.pathname.startsWith("/research") ||
    url.pathname.startsWith("/analytics") ||
    url.pathname.startsWith("/monitoring") ||
    url.pathname.startsWith("/integrations") ||
    url.pathname.startsWith("/settings")
  );
}

function isExpired(response, maxAge) {
  const dateHeader = response.headers.get("date");
  if (!dateHeader) return false;

  const responseDate = new Date(dateHeader);
  const now = new Date();

  return now.getTime() - responseDate.getTime() > maxAge;
}

async function cleanupCache(cacheName, maxEntries) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();

  if (keys.length > maxEntries) {
    // Remove oldest entries (simple FIFO)
    const keysToDelete = keys.slice(0, keys.length - maxEntries);
    await Promise.all(keysToDelete.map((key) => cache.delete(key)));
  }
}

// Message handling for cache management
self.addEventListener("message", (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case "SKIP_WAITING":
      self.skipWaiting();
      break;

    case "CLEAR_CACHE":
      clearCache(payload?.cacheName);
      break;

    case "WARM_CACHE":
      warmCache(payload?.urls || []);
      break;

    case "GET_CACHE_STATUS":
      getCacheStatus().then((status) => {
        event.ports[0]?.postMessage({ type: "CACHE_STATUS", payload: status });
      });
      break;

    default:
      console.log("[SW] Unknown message type:", type);
  }
});

// Cache management functions
async function clearCache(cacheName) {
  try {
    if (cacheName) {
      await caches.delete(cacheName);
      console.log(`[SW] Cleared cache: ${cacheName}`);
    } else {
      // Clear all caches
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map((name) => caches.delete(name)));
      console.log("[SW] Cleared all caches");
    }
  } catch (error) {
    console.error("[SW] Cache clearing failed:", error);
  }
}

async function warmCache(urls) {
  try {
    const cache = await caches.open(RUNTIME_CACHE);

    const warmPromises = urls.map(async (url) => {
      try {
        const response = await fetch(url);
        if (response.ok) {
          await cache.put(url, response);
        }
      } catch (error) {
        console.log(`[SW] Failed to warm cache for ${url}:`, error);
      }
    });

    await Promise.all(warmPromises);
    console.log(`[SW] Warmed cache for ${urls.length} URLs`);
  } catch (error) {
    console.error("[SW] Cache warming failed:", error);
  }
}

async function getCacheStatus() {
  try {
    const cacheNames = await caches.keys();
    const status = {};

    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const keys = await cache.keys();
      status[cacheName] = {
        entryCount: keys.length,
        urls: keys.map((request) => request.url),
      };
    }

    return status;
  } catch (error) {
    console.error("[SW] Failed to get cache status:", error);
    return {};
  }
}

// Offline page handling
self.addEventListener("fetch", (event) => {
  // Handle navigation requests when offline
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(async () => {
        const cache = await caches.open(RUNTIME_CACHE);
        const offlinePage = await cache.match("/");
        return (
          offlinePage ||
          new Response("Offline - Please check your connection", {
            status: 503,
            statusText: "Service Unavailable",
          })
        );
      })
    );
  }
});

console.log("[SW] Service worker script loaded");
