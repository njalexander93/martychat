import { isTokenExpired, refreshTokens, isAuthenticated, handleLogout, checkAndRefreshAuth } from '@/utils/auth';

// Mock localStorage and sessionStorage
const localStorageMock = (function () {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

const sessionStorageMock = (function () {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
  };
})();

// Mock fetch function
global.fetch = jest.fn();

describe('Auth Utilities', () => {
  // Save original objects
  const originalLocalStorage = global.localStorage;
  const originalSessionStorage = global.sessionStorage;
  const originalLocation = global.location;

  beforeEach(() => {
    // Set up mocks before each test
    Object.defineProperty(window, 'localStorage', { value: localStorageMock });
    Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });
    delete window.location;
    window.location = { href: '' };

    // Clear mocks for fresh start
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  afterAll(() => {
    // Restore original objects after all tests
    Object.defineProperty(window, 'localStorage', { value: originalLocalStorage });
    Object.defineProperty(window, 'sessionStorage', { value: originalSessionStorage });
    window.location = originalLocation;
  });

  describe('isTokenExpired', () => {
    test('returns true when no expiration times exist', () => {
      expect(isTokenExpired()).toBe(true);
    });

    test('returns true when refresh token is expired', () => {
      const now = new Date().getTime();
      const pastTime = now - 10000; // 10 seconds in the past

      localStorageMock.setItem('idTokenExpires', now + 3600000); // 1 hour in the future
      localStorageMock.setItem('accessTokenExpires', now + 3600000);
      localStorageMock.setItem('refreshTokenExpires', pastTime);

      expect(isTokenExpired()).toBe(true);
    });

    test('returns true when tokens are about to expire (within 5 minutes)', () => {
      const now = new Date().getTime();
      const almostExpiredTime = now + 4 * 60 * 1000; // 4 minutes in the future (less than 5 min)
      const notExpiredTime = now + 10 * 60 * 1000; // 10 minutes in the future

      localStorageMock.setItem('idTokenExpires', almostExpiredTime);
      localStorageMock.setItem('accessTokenExpires', notExpiredTime);
      localStorageMock.setItem('refreshTokenExpires', notExpiredTime);

      expect(isTokenExpired()).toBe(true);
    });

    test('returns false when tokens are not expired or about to expire', () => {
      const now = new Date().getTime();
      const futureTime = now + 3600000; // 1 hour in the future

      localStorageMock.setItem('idTokenExpires', futureTime);
      localStorageMock.setItem('accessTokenExpires', futureTime);
      localStorageMock.setItem('refreshTokenExpires', futureTime);

      expect(isTokenExpired()).toBe(false);
    });
  });

  // You can add more tests for other functions here
});
