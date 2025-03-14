/**
 * @fileoverview Unit tests for the authentication utilities in MartyChat.
 * These tests validate token management, session handling, and authentication state management.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import { isTokenExpired, refreshTokens, isAuthenticated, handleLogout, checkAndRefreshAuth } from '@/utils/auth';

// Mock global fetch
global.fetch = jest.fn();

// Mock localStorage
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
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock sessionStorage
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
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

// Mock window.location
delete window.location;
window.location = {
  href: '',
  pathname: '/marty',
};

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});

/**
 * Unit tests for the Authentication Utilities.
 */
describe('Authentication Utilities', () => {
  // Clear all mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    sessionStorageMock.clear();
    document.cookie = '';
    window.location.href = '';
    window.location.pathname = '/marty';
  });

  /**
   * Tests for the isTokenExpired function
   */
  describe('isTokenExpired function', () => {
    /**
     * Test that isTokenExpired returns true when no tokens exist.
     */
    test('returns true when no tokens exist', () => {
      // Setup: Ensure no tokens in localStorage
      localStorageMock.clear();

      const result = isTokenExpired();

      expect(result).toBe(true);
    });

    /**
     * Test that isTokenExpired returns true when refresh token is expired.
     */
    test('returns true when refresh token is expired', () => {
      // Setup: Set refresh token to be expired (past time)
      const pastTime = new Date().getTime() - 1000; // 1 second ago
      localStorageMock.setItem('refreshTokenExpires', pastTime);
      localStorageMock.setItem('idTokenExpires', new Date().getTime() + 3600000); // 1 hour in future
      localStorageMock.setItem('accessTokenExpires', new Date().getTime() + 3600000); // 1 hour in future

      const result = isTokenExpired();

      expect(result).toBe(true);
    });

    /**
     * Test that isTokenExpired returns true when ID token is about to expire.
     */
    test('returns true when ID token is about to expire (within 5 minutes)', () => {
      // Setup: Set ID token to expire soon (4 minutes from now)
      const fourMinutes = 4 * 60 * 1000;
      const futureTime = new Date().getTime() + fourMinutes;
      localStorageMock.setItem('idTokenExpires', futureTime);
      localStorageMock.setItem('accessTokenExpires', new Date().getTime() + 3600000); // 1 hour in future
      localStorageMock.setItem('refreshTokenExpires', new Date().getTime() + 86400000); // 1 day in future

      const result = isTokenExpired();

      expect(result).toBe(true);
    });

    /**
     * Test that isTokenExpired returns true when access token is about to expire.
     */
    test('returns true when access token is about to expire (within 5 minutes)', () => {
      // Setup: Set access token to expire soon (4 minutes from now)
      const fourMinutes = 4 * 60 * 1000;
      const futureTime = new Date().getTime() + fourMinutes;
      localStorageMock.setItem('accessTokenExpires', futureTime);
      localStorageMock.setItem('idTokenExpires', new Date().getTime() + 3600000); // 1 hour in future
      localStorageMock.setItem('refreshTokenExpires', new Date().getTime() + 86400000); // 1 day in future

      const result = isTokenExpired();

      expect(result).toBe(true);
    });

    /**
     * Test that isTokenExpired returns false when all tokens are valid.
     */
    test('returns false when all tokens are valid and not near expiration', () => {
      // Setup: Set all tokens to be valid (over 5 minutes until expiration)
      const oneHour = 60 * 60 * 1000;
      const futureTime = new Date().getTime() + oneHour;
      localStorageMock.setItem('idTokenExpires', futureTime);
      localStorageMock.setItem('accessTokenExpires', futureTime);
      localStorageMock.setItem('refreshTokenExpires', new Date().getTime() + 86400000); // 1 day in future

      const result = isTokenExpired();

      expect(result).toBe(false);
    });
  });

  /**
   * Tests for the refreshTokens function
   */
  describe('refreshTokens function', () => {
    /**
     * Test that refreshTokens returns false when no refresh token exists.
     */
    test('returns false when no refresh token exists', async () => {
      // Setup: Ensure no refresh token in localStorage
      localStorageMock.clear();

      const result = await refreshTokens();

      expect(result).toBe(false);
      expect(fetch).not.toHaveBeenCalled();
    });

    /**
     * Test that refreshTokens returns false when no user ID exists.
     */
    test('returns false when no user ID exists', async () => {
      // Setup: Set refresh token but no user ID
      localStorageMock.setItem('refreshToken', 'test-refresh-token');
      sessionStorageMock.clear(); // Ensure no userId in sessionStorage

      const result = await refreshTokens();

      expect(result).toBe(false);
      expect(fetch).not.toHaveBeenCalled();
    });

    /**
     * Test that refreshTokens handles successful token refresh.
     */
    test('successfully refreshes tokens', async () => {
      // Setup: Set refresh token and user ID
      localStorageMock.setItem('refreshToken', 'test-refresh-token');
      sessionStorageMock.setItem('userId', 'test-user-id');

      // Mock successful response from refresh endpoint
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          authenticationResult: {
            idToken: 'new-id-token',
            accessToken: 'new-access-token',
            idTokenExpires: 3600, // 1 hour in seconds
            accessTokenExpires: 3600, // 1 hour in seconds
          },
        }),
      });

      const result = await refreshTokens();

      // Check result and fetch call
      expect(result).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        '/api/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            refreshToken: 'test-refresh-token',
            userId: 'test-user-id',
          }),
        })
      );

      // Verify tokens and expiration times were updated in localStorage
      expect(localStorageMock.setItem).toHaveBeenCalledWith('idToken', 'new-id-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('accessToken', 'new-access-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('idTokenExpires', expect.any(Number));
      expect(localStorageMock.setItem).toHaveBeenCalledWith('accessTokenExpires', expect.any(Number));

      // Verify cookie was updated
      expect(document.cookie).toContain('idToken=new-id-token');
    });

    /**
     * Test that refreshTokens handles API errors gracefully.
     */
    test('returns false and handles API errors', async () => {
      // Setup: Set refresh token and user ID
      localStorageMock.setItem('refreshToken', 'test-refresh-token');
      sessionStorageMock.setItem('userId', 'test-user-id');

      // Mock failed response from refresh endpoint
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({
          error: 'Invalid refresh token',
        }),
      });

      // Mock console.error to prevent noise in test output
      console.error = jest.fn();

      const result = await refreshTokens();

      // Check result
      expect(result).toBe(false);
      expect(console.error).toHaveBeenCalledWith('Error refreshing tokens:', expect.any(Error));
    });

    /**
     * Test that refreshTokens handles network errors gracefully.
     */
    test('returns false and handles network errors', async () => {
      // Setup: Set refresh token and user ID
      localStorageMock.setItem('refreshToken', 'test-refresh-token');
      sessionStorageMock.setItem('userId', 'test-user-id');

      // Mock network error
      fetch.mockRejectedValueOnce(new Error('Network error'));

      // Mock console.error to prevent noise in test output
      console.error = jest.fn();

      const result = await refreshTokens();

      // Check result
      expect(result).toBe(false);
      expect(console.error).toHaveBeenCalledWith('Error refreshing tokens:', expect.any(Error));
    });
  });

  /**
   * Tests for the isAuthenticated function
   */
  describe('isAuthenticated function', () => {
    /**
     * Test that isAuthenticated returns false when no user ID exists.
     */
    test('returns false when no user ID exists', () => {
      // Setup: Set ID token but no user ID
      localStorageMock.setItem('idToken', 'test-id-token');
      sessionStorageMock.clear(); // Ensure no userId in sessionStorage

      const result = isAuthenticated();

      expect(result).toBe(false);
    });

    /**
     * Test that isAuthenticated returns false when no ID token exists.
     */
    test('returns false when no ID token exists', () => {
      // Setup: Set user ID but no ID token
      sessionStorageMock.setItem('userId', 'test-user-id');
      localStorageMock.clear(); // Ensure no idToken in localStorage

      const result = isAuthenticated();

      expect(result).toBe(false);
    });

    /**
     * Test that isAuthenticated returns true when both user ID and ID token exist.
     */
    test('returns true when both user ID and ID token exist', () => {
      // Setup: Set both user ID and ID token
      sessionStorageMock.setItem('userId', 'test-user-id');
      localStorageMock.setItem('idToken', 'test-id-token');

      const result = isAuthenticated();

      expect(result).toBe(true);
    });
  });

  /**
   * Tests for the handleLogout function
   */
  describe('handleLogout function', () => {
    /**
     * Test that handleLogout clears all auth data and redirects to login.
     */
    test('clears all auth data and redirects to login', () => {
      // Setup: Set all auth data
      sessionStorageMock.setItem('userId', 'test-user-id');
      localStorageMock.setItem('idToken', 'test-id-token');
      localStorageMock.setItem('accessToken', 'test-access-token');
      localStorageMock.setItem('refreshToken', 'test-refresh-token');
      localStorageMock.setItem('idTokenExpires', '12345');
      localStorageMock.setItem('accessTokenExpires', '12345');
      localStorageMock.setItem('refreshTokenExpires', '12345');
      document.cookie = 'idToken=test-id-token; path=/';

      // Call handleLogout with default redirect path
      handleLogout();

      // Verify all storage items were removed
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith('userId');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('idToken');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('accessToken');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refreshToken');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('idTokenExpires');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('accessTokenExpires');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refreshTokenExpires');

      // Verify cookie was cleared
      expect(document.cookie).toMatch(/idToken=;.*expires=Thu, 01 Jan 1970/);

      // Verify redirect
      expect(window.location.href).toBe('/login?callbackUrl=%2F');
    });

    /**
     * Test that handleLogout uses the provided redirect path.
     */
    test('uses the provided redirect path', () => {
      // Call handleLogout with custom redirect path
      handleLogout('/dashboard');

      // Verify redirect with custom path
      expect(window.location.href).toBe('/login?callbackUrl=%2Fdashboard');
    });
  });

  /**
   * Tests for the checkAndRefreshAuth function
   */
  describe('checkAndRefreshAuth function', () => {
    /**
     * Test that checkAndRefreshAuth returns false and redirects when not authenticated.
     */
    test('returns false and redirects when not authenticated', async () => {
      // Setup: Ensure not authenticated
      localStorageMock.clear();
      sessionStorageMock.clear();

      const result = await checkAndRefreshAuth();

      expect(result).toBe(false);
      // Verify redirect to login with current path
      expect(window.location.href).toBe('/login?callbackUrl=%2Fmarty');
    });

    /**
     * Test that checkAndRefreshAuth returns true when authenticated with valid tokens.
     */
    test('returns true when authenticated with valid tokens', async () => {
      // Setup: Authenticated with valid tokens
      sessionStorageMock.setItem('userId', 'test-user-id');
      localStorageMock.setItem('idToken', 'test-id-token');

      // Set token expiration times far in the future
      const oneDay = 24 * 60 * 60 * 1000;
      const futureTime = new Date().getTime() + oneDay;
      localStorageMock.setItem('idTokenExpires', futureTime);
      localStorageMock.setItem('accessTokenExpires', futureTime);
      localStorageMock.setItem('refreshTokenExpires', futureTime);

      const result = await checkAndRefreshAuth();

      expect(result).toBe(true);
      // Verify no redirect occurred
      expect(window.location.href).toBe('');
    });

    /**
     * Test that checkAndRefreshAuth refreshes tokens when they are about to expire.
     */
    test('refreshes tokens when they are about to expire', async () => {
      // Setup: Authenticated but tokens about to expire
      sessionStorageMock.setItem('userId', 'test-user-id');
      localStorageMock.setItem('idToken', 'test-id-token');
      localStorageMock.setItem('refreshToken', 'test-refresh-token');

      // Set expiration times to be in the past or very close to now (to trigger refresh)
      const pastTime = new Date().getTime() - 1000; // 1 second ago
      localStorageMock.setItem('idTokenExpires', pastTime.toString());
      localStorageMock.setItem('accessTokenExpires', pastTime.toString());

      // Set refresh token to still be valid (future time)
      const futureTime = new Date().getTime() + 24 * 60 * 60 * 1000; // 1 day in future
      localStorageMock.setItem('refreshTokenExpires', futureTime.toString());

      // Mock successful response from refresh endpoint
      fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          authenticationResult: {
            idToken: 'new-id-token',
            accessToken: 'new-access-token',
            idTokenExpires: 3600, // 1 hour in seconds
            accessTokenExpires: 3600, // 1 hour in seconds
          },
        }),
      });

      const result = await checkAndRefreshAuth();

      expect(result).toBe(true);
      // Verify fetch was called (indication that refreshTokens was called)
      expect(fetch).toHaveBeenCalledWith(
        '/api/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('test-refresh-token'),
        })
      );
      // Verify no redirect occurred
      expect(window.location.href).toBe('');
    });

    /**
     * Test that checkAndRefreshAuth handles token refresh failure.
     */
    test('redirects to login when token refresh fails', async () => {
      // Setup: Authenticated but tokens about to expire
      sessionStorageMock.setItem('userId', 'test-user-id');
      localStorageMock.setItem('idToken', 'test-id-token');
      localStorageMock.setItem('refreshToken', 'test-refresh-token');

      // Set expiration times to be in the past (to trigger refresh)
      const pastTime = new Date().getTime() - 1000; // 1 second ago
      localStorageMock.setItem('idTokenExpires', pastTime.toString());
      localStorageMock.setItem('accessTokenExpires', pastTime.toString());

      // Set refresh token to still be valid (future time)
      const futureTime = new Date().getTime() + 24 * 60 * 60 * 1000; // 1 day in future
      localStorageMock.setItem('refreshTokenExpires', futureTime.toString());

      // Mock failed response from refresh endpoint
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({
          error: 'Invalid refresh token',
        }),
      });

      const result = await checkAndRefreshAuth();

      expect(result).toBe(false);
      // Verify fetch was called (indication that refreshTokens was called)
      expect(fetch).toHaveBeenCalled();
      // Verify redirect to login
      expect(window.location.href).toBe('/login?callbackUrl=%2Fmarty');
    });
  });
});
