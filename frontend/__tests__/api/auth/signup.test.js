/**
 * @fileoverview Unit tests for the Signup API Route in MartyChat.
 * These tests validate CORS handling in OPTIONS requests and
 * input validation for the POST signup request.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

// Set test environment
process.env.NODE_ENV = 'development';
process.env.NEXT_PUBLIC_LAMBDA_URL = 'http://localhost:9000';

// Import necessary modules
const { POST, OPTIONS, requestCounts } = require('@/app/api/auth/signup/route');

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

/**
 * Unit tests for the Signup API Route.
 */
describe('Signup API Route', () => {
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

  /**
   * Tests for the POST signup request handler
   */
  describe('POST handler', () => {
    /**
     * Test that the POST handler returns a 400 error when required fields are missing.
     */
    test('returns 400 when required fields are missing', async () => {
      // Create a mock request with missing fields
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '127.0.0.1' : null)),
        },
        json: jest.fn().mockResolvedValue({
          email: 'test@example.com',
          // Missing password, firstName, lastName
        }),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(400);
      expect(response.body).toEqual({ error: 'All required fields must be filled.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler returns a 400 error for invalid email format.
     */
    test('returns 400 for invalid email format', async () => {
      // Create a mock request with invalid email
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '127.0.0.1' : null)),
        },
        json: jest.fn().mockResolvedValue({
          email: 'invalid-email', // Invalid email format
          password: 'Test1234!',
          firstName: 'Test',
          lastName: 'User',
        }),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(400);
      expect(response.body).toEqual({ error: 'Invalid email format.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler successfully forwards the request to the Lambda function.
     */
    test('successfully forwards signup request to Lambda function', async () => {
      process.env.NODE_ENV = 'development'; // Change environment to ensure fetch is used

      // Mock successful Lambda response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          message: 'User created successfully!',
          user: 'test-user-id',
        }),
      });

      // Set up request with valid data
      const mockRequest = {
        headers: { get: jest.fn(() => '192.168.1.1') },
        json: jest.fn().mockResolvedValue({
          email: 'test@example.com',
          password: 'Test1234!',
          firstName: 'Test',
          lastName: 'User',
          organization: 'Test Org',
        }),
      };

      const response = await POST(mockRequest);

      // Verify Lambda was called correctly
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:9000/api/auth/signup',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'Test1234!',
            firstName: 'Test',
            lastName: 'User',
            organization: 'Test Org',
          }),
        })
      );

      // Restore environment
      process.env.NODE_ENV = 'development';

      // Verify response
      expect(response.status).toBe(200);
    });

    /**
     * Test that the POST handler handles previously used password error.
     */
    test('handles previously used password error', async () => {
      // Mock Lambda error response for previously used password
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({
          error: 'Password has previously been used for this account.',
        }),
      });

      // Set up request
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '192.168.1.3' : null)),
        },
        json: jest.fn().mockResolvedValue({
          email: 'test@example.com',
          password: 'PreviouslyUsed123!',
          firstName: 'Test',
          lastName: 'User',
        }),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(400);
      expect(response.body).toEqual({
        error: 'This password has been previously used for an account with this email address.',
      });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler handles authentication error.
     */
    test('handles authentication error', async () => {
      // Mock Lambda authentication error
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: jest.fn().mockResolvedValue({
          message: 'Unauthorized access to Lambda function',
        }),
      });

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

      const response = await POST(mockRequest);

      expect(response.status).toBe(403);
      expect(response.body).toEqual({ error: 'Authentication error.' });
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
      const requestCountsExport = require('@/app/api/auth/signup/route').requestCounts;
      // If requestCounts is not exported, we'll need to set up the test differently
      if (requestCountsExport) {
        requestCountsExport.set(ip, Array(6).fill(now)); // 6 requests in current minute (over limit of 5)
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

    /**
     * Test that the POST handler handles unexpected errors.
     */
    test('handles unexpected errors', async () => {
      // Mock fetch failure
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      // Set up request
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '192.168.1.6' : null)),
        },
        json: jest.fn().mockResolvedValue({
          email: 'test@example.com',
          password: 'Test1234!',
          firstName: 'Test',
          lastName: 'User',
        }),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(500);
      expect(response.body).toEqual({ error: 'Internal server error.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(console.error).toHaveBeenCalledWith('Signup Error:', expect.any(Error));
    });

    /**
     * Test that the POST handler handles JSON parsing errors.
     */
    test('handles JSON parsing errors', async () => {
      // Mock JSON error response
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({
          error: 'Invalid JSON',
        }),
      });

      // Set up request with JSON parsing error

      // Create a mock request with JSON parsing error
      const mockRequest = {
        headers: {
          get: jest.fn((header) => (header === 'x-forwarded-for' ? '127.0.0.1' : null)),
        },
        json: jest.fn().mockRejectedValueOnce(new Error('Invalid JSON')),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(400);
      expect(response.body).toEqual({ error: 'Invalid request format.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });
  });
});
