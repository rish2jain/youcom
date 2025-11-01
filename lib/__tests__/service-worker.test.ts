/**
 * Tests for Service Worker management system
 */

import serviceWorkerManager, {
  getCriticalResources,
  getRouteResources,
} from "../service-worker";

// Mock service worker APIs
const mockServiceWorker = {
  register: jest.fn(),
  unregister: jest.fn(),
  update: jest.fn(),
  controller: null,
  addEventListener: jest.fn(),
  postMessage: jest.fn(),
};

const mockRegistration = {
  installing: null,
  waiting: null,
  active: null,
  scope: "/",
  update: jest.fn(),
  unregister: jest.fn(),
  addEventListener: jest.fn(),
};

const mockCaches = {
  open: jest.fn(),
  delete: jest.fn(),
  keys: jest.fn(),
  match: jest.fn(),
};

const mockCache = {
  add: jest.fn(),
  addAll: jest.fn(),
  put: jest.fn(),
  match: jest.fn(),
  delete: jest.fn(),
  keys: jest.fn(),
};

// Setup global mocks
Object.defineProperty(global, "navigator", {
  value: {
    serviceWorker: mockServiceWorker,
  },
  writable: true,
});

Object.defineProperty(global, "caches", {
  value: mockCaches,
  writable: true,
});

Object.defineProperty(global, "window", {
  value: {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  },
  writable: true,
});

describe("Service Worker Manager", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockServiceWorker.register.mockResolvedValue(mockRegistration);
    mockCaches.open.mockResolvedValue(mockCache);
    mockCaches.keys.mockResolvedValue(["cache1", "cache2"]);
    mockCache.keys.mockResolvedValue([]);
  });

  describe("isSupported", () => {
    it("should return true when service worker is supported", () => {
      expect(serviceWorkerManager.isSupported()).toBe(true);
    });

    it("should return false when service worker is not supported", () => {
      const originalNavigator = global.navigator;
      // @ts-ignore
      delete global.navigator.serviceWorker;

      expect(serviceWorkerManager.isSupported()).toBe(false);

      global.navigator = originalNavigator;
    });
  });

  describe("register", () => {
    it("should register service worker successfully", async () => {
      const registration = await serviceWorkerManager.register();

      expect(mockServiceWorker.register).toHaveBeenCalledWith("/sw.js", {
        scope: "/",
        updateViaCache: "none",
      });
      expect(registration).toBe(mockRegistration);
    });

    it("should handle registration failure", async () => {
      mockServiceWorker.register.mockRejectedValueOnce(
        new Error("Registration failed")
      );

      const registration = await serviceWorkerManager.register();

      expect(registration).toBeNull();
    });

    it("should not register if not supported", async () => {
      const originalNavigator = global.navigator;
      // @ts-ignore
      delete global.navigator.serviceWorker;

      const registration = await serviceWorkerManager.register();

      expect(registration).toBeNull();
      expect(mockServiceWorker.register).not.toHaveBeenCalled();

      global.navigator = originalNavigator;
    });
  });

  describe("unregister", () => {
    it("should unregister service worker successfully", async () => {
      // First register
      await serviceWorkerManager.register();

      mockRegistration.unregister.mockResolvedValueOnce(true);

      const result = await serviceWorkerManager.unregister();

      expect(mockRegistration.unregister).toHaveBeenCalled();
      expect(result).toBe(true);
    });

    it("should return false if no registration exists", async () => {
      const result = await serviceWorkerManager.unregister();

      expect(result).toBe(false);
    });
  });

  describe("clearCache", () => {
    it("should clear specific cache", async () => {
      mockCaches.delete.mockResolvedValueOnce(true);

      await serviceWorkerManager.clearCache("test-cache");

      expect(mockCaches.delete).toHaveBeenCalledWith("test-cache");
    });

    it("should clear all caches when no cache name provided", async () => {
      mockCaches.keys.mockResolvedValueOnce(["cache1", "cache2"]);
      mockCaches.delete.mockResolvedValue(true);

      await serviceWorkerManager.clearCache();

      expect(mockCaches.delete).toHaveBeenCalledWith("cache1");
      expect(mockCaches.delete).toHaveBeenCalledWith("cache2");
    });

    it("should handle cache clearing errors", async () => {
      mockCaches.delete.mockRejectedValueOnce(new Error("Delete failed"));

      await expect(
        serviceWorkerManager.clearCache("test-cache")
      ).rejects.toThrow("Delete failed");
    });
  });

  describe("warmCache", () => {
    it("should warm cache with provided URLs", async () => {
      const urls = ["/page1", "/page2", "/api/data"];

      // Mock fetch responses
      global.fetch = jest
        .fn()
        .mockResolvedValueOnce(new Response("page1 content"))
        .mockResolvedValueOnce(new Response("page2 content"))
        .mockResolvedValueOnce(new Response("api data"));

      await serviceWorkerManager.warmCache(urls);

      expect(global.fetch).toHaveBeenCalledTimes(3);
      expect(global.fetch).toHaveBeenCalledWith("/page1");
      expect(global.fetch).toHaveBeenCalledWith("/page2");
      expect(global.fetch).toHaveBeenCalledWith("/api/data");
    });

    it("should handle warming failures gracefully", async () => {
      const urls = ["/success", "/failure"];

      global.fetch = jest
        .fn()
        .mockResolvedValueOnce(new Response("success"))
        .mockRejectedValueOnce(new Error("Network error"));

      // Should not throw
      await serviceWorkerManager.warmCache(urls);

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe("getCacheStatus", () => {
    it("should return cache status information", async () => {
      mockCaches.keys.mockResolvedValueOnce(["cache1", "cache2"]);
      mockCache.keys
        .mockResolvedValueOnce([new Request("/url1"), new Request("/url2")])
        .mockResolvedValueOnce([new Request("/url3")]);

      const status = await serviceWorkerManager.getCacheStatus();

      expect(status).toEqual({
        cache1: {
          entryCount: 2,
          urls: ["/url1", "/url2"],
        },
        cache2: {
          entryCount: 1,
          urls: ["/url3"],
        },
      });
    });

    it("should handle cache status errors", async () => {
      mockCaches.keys.mockRejectedValueOnce(new Error("Cache access failed"));

      const status = await serviceWorkerManager.getCacheStatus();

      expect(status).toEqual({});
    });
  });
});

describe("Cache Resource Utilities", () => {
  describe("getCriticalResources", () => {
    it("should return array of critical resource URLs", () => {
      const resources = getCriticalResources();

      expect(Array.isArray(resources)).toBe(true);
      expect(resources.length).toBeGreaterThan(0);
      expect(resources).toContain("/");
      expect(resources).toContain("/dashboard");
    });
  });

  describe("getRouteResources", () => {
    it("should return route-specific resources for dashboard", () => {
      const resources = getRouteResources("/dashboard");

      expect(Array.isArray(resources)).toBe(true);
      expect(resources.some((r) => r.includes("dashboard"))).toBe(true);
    });

    it("should return route-specific resources for research", () => {
      const resources = getRouteResources("/research");

      expect(Array.isArray(resources)).toBe(true);
      expect(resources.some((r) => r.includes("research"))).toBe(true);
      expect(resources.some((r) => r.includes("charts"))).toBe(true);
    });

    it("should return route-specific resources for analytics", () => {
      const resources = getRouteResources("/analytics");

      expect(Array.isArray(resources)).toBe(true);
      expect(resources.some((r) => r.includes("analytics"))).toBe(true);
      expect(resources.some((r) => r.includes("charts"))).toBe(true);
    });

    it("should return base resources for unknown routes", () => {
      const resources = getRouteResources("/unknown");

      expect(Array.isArray(resources)).toBe(true);
      expect(resources.length).toBeGreaterThan(0);
    });
  });
});
