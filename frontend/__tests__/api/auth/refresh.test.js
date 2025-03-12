/**
 * @fileoverview Unit tests for the Refresh API Route in MartyChat.
 * These tests validate CORS handling in OPTIONS requests and
 * input validation for the POST refresh request.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-03-11
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

const { POST, OPTIONS, requestCounts } = require('@/app/api/auth/refresh/route');

// Set environment variables for testing
process.env.NEXT_PUBLIC_LAMBDA_URL = 'http://localhost:9000';

// Create NextResponse mock
jest.mock('next/server', () => {
  return {
    NextResponse: class {
      constructor(body, options = {}) {
        this.body = body;
        this.status = options.status || 200;
        this.headers = new Map(Object.entries(options.headers || {}));
      }

      json() {
        return Promise.resolve(this.body);
      }

      text() {
        return Promise.resolve(this.body);
      }

      static json(body, options = {}) {
        return new this(body, options);
      }
    },
  };
});

// Mock global fetch
global.fetch = jest.fn();

// Mock console methods
console.error = jest.fn();
console.log = jest.fn();

describe('Refresh Token API Route', () => {
  // Clear mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();

    if (requestCounts) {
      requestCounts.clear();
    }
  });

  /**
   * Tests for the OPTIONS request handler
   */
  describe('OPTIONS handler', () => {
    /**
     * Test that the OPTIONS request handler returns the correct CORS headers.
     */
    test('returns correct CORS headers', async () => {
      const response = await OPTIONS();

      expect(response.status).toBe(204);
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(response.headers.get('Access-Control-Allow-Methods')).toBe('POST, OPTIONS');
      expect(response.headers.get('Access-Control-Allow-Headers')).toBe('Content-Type, Authorization');
    });
  });

  describe('POST handler', () => {
    test('returns 400 when refreshToken is missing', async () => {
      // Create a request with missing refreshToken
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '127.0.0.1' : null)),
        },
        json: jest.fn().mockResolvedValue({ userId: 'test-user-id' }), // Missing refreshToken
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(400);
      expect(response.body).toEqual({ error: 'Refresh token is required.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    test('returns 400 when userId is missing', async () => {
      // Create a request with missing userId
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '127.0.0.1' : null)),
        },
        json: jest.fn().mockResolvedValue({ refreshToken: 'test-refresh-token' }), // Missing userId
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(400);
      expect(response.body).toEqual({ error: 'User ID is required.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    test('successfully forwards refresh request to Lambda function', async () => {
      // Mock successful Lambda response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          message: 'Tokens refreshed successfully.',
          authenticationResult: {
            AccessToken: 'new-access-token',
            IdToken: 'new-id-token',
            ExpiresIn: 3600,
            RefreshTokenExpires: 2592000,
          },
        }),
      });

      // Set up request
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '192.168.1.1' : null)),
        },
        json: jest.fn().mockResolvedValue({
          refreshToken: 'test-refresh-token',
          userId: 'test-user-id',
        }),
      };

      const response = await POST(mockRequest);

      // Verify Lambda was called correctly
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:9000/api/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            refreshToken: 'test-refresh-token',
            userId: 'test-user-id',
          }),
        })
      );

      // Verify response
      expect(response.status).toBe(200);
      expect(response.body).toEqual(
        expect.objectContaining({
          message: 'Tokens refreshed successfully.',
          authenticationResult: expect.objectContaining({
            AccessToken: 'new-access-token',
            IdToken: 'new-id-token',
          }),
        })
      );
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    test('handles Lambda error responses', async () => {
      // Mock Lambda error response
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({
          error: 'Refresh token is invalid or expired.',
        }),
      });

      // Set up request
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '192.168.1.2' : null)),
        },
        json: jest.fn().mockResolvedValue({
          refreshToken: 'invalid-refresh-token',
          userId: 'test-user-id',
        }),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(401);
      expect(response.body).toEqual({ error: 'Refresh token is invalid or expired.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler handles rate limiting.
     */
    test('handles rate limiting', async () => {
      // Set up request
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '127.0.0.1' : null)),
        },
        json: jest.fn().mockResolvedValue({
          email: 'test@example.com',
          password: 'Test1234!',
          firstName: 'Test',
          lastName: 'User',
        }),
      };

      // Simulate exceeding rate limit by pre-populating request counts
      // This directly manipulates the module's internal rate limiting state
      const ip = '127.0.0.1';
      const now = Date.now();
      const requestCountsExport = require('@/app/api/auth/refresh/route').requestCounts;
      // If requestCounts is not exported, we'll need to set up the test differently
      if (requestCountsExport) {
        requestCountsExport.set(ip, Array(11).fill(now)); // 11 requests in current minute (over limit of 5)
      } else {
        // Skip this test if we can't manipulate the requestCounts
        console.log('Skipping rate limit test as requestCounts is not exported');
        return;
      }

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(429);
      expect(responseBody).toEqual({ error: 'Rate limit exceeded. Please try again later.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    test('handles unexpected errors', async () => {
      // Mock fetch failure
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      // Set up request
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '192.168.1.3' : null)),
        },
        json: jest.fn().mockResolvedValue({
          refreshToken: 'test-refresh-token',
          userId: 'test-user-id',
        }),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(500);
      expect(response.body).toEqual({ error: 'Internal server error.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(console.error).toHaveBeenCalledWith('Refresh Error:', expect.any(Error));
    });

    test('handles JSON parsing errors', async () => {
      // Set up request with JSON parsing error
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '127.0.0.1' : null)),
        },
        json: jest.fn().mockRejectedValueOnce(new Error('Invalid JSON')),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(400);
      expect(response.body).toEqual({ error: 'Invalid JSON format.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });
  });
});
