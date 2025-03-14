/**
 * @fileoverview Unit tests for the Marty Chat API Route in MartyChat.
 * These tests validate CORS handling, authentication requirements, and
 * request/response processing for chat interactions.
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
const { POST, OPTIONS, GET, requestCounts } = require('@/app/api/v1/marty/route');

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
 * Unit tests for the Marty Chat API Route
 */
describe('Marty Chat API Route', () => {
  let testIpCounter = 0;

  // Clear mocks before each test
  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();

    // Increment the test IP counter for unique IP addresses on each test
    testIpCounter++;

    // Clear request counts
    if (requestCounts) {
      // Create a new Map instead of clearing the existing one
      Object.defineProperty(require('@/app/api/v1/marty/route'), 'requestCounts', {
        value: new Map(),
        writable: true,
      });
    }

    // Default mock fetch to return a successful response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: jest.fn().mockResolvedValue({
          response: "I'm Marty, how can I help with psychology?",
          conversation_id: 'test-conversation-123',
        }),
      })
    );
  });

  /**
   * Tests for the OPTIONS request handler
   */
  describe('OPTIONS handler', () => {
    /**
     * Test that the OPTIONS request handler returns the correct CORS headers
     */
    test('returns correct CORS headers', async () => {
      const response = await OPTIONS();

      expect(response.status).toBe(204);
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(response.headers.get('Access-Control-Allow-Methods')).toBe('POST, OPTIONS, GET');
      expect(response.headers.get('Access-Control-Allow-Headers')).toBe('Content-Type, Authorization');
    });
  });

  /**
   * Tests for the POST request handler
   */
  describe('POST handler', () => {
    /**
     * Test that the POST handler requires authentication
     */
    test('requires authentication', async () => {
      // Create a mock request with no authorization header
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            return null; // No authorization header
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: 'Hello Marty',
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(401);
      expect(responseBody).toEqual({ error: 'Authentication required.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler validates required fields
     */
    test('validates user_id is required', async () => {
      // Create a mock request with authorization but missing user_id
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: 'Hello Marty',
          // Missing user_id
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(400);
      expect(responseBody).toEqual({ error: 'User ID is required.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler validates message is required
     */
    test('validates message is required', async () => {
      // Create a mock request with authorization but missing message
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          // Missing message
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(400);
      expect(responseBody).toEqual({ error: 'Message is required.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler validates message data type
     */
    test('validates message data type', async () => {
      // Create a mock request with authorization but non-string message
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: { text: 'This is an object, not a string' }, // Wrong type
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(400);
      expect(responseBody).toEqual({ error: 'Message is of the wrong data type.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler successfully processes a valid chat request
     */
    test('successfully processes valid chat request', async () => {
      // Create a mock request with valid data
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: 'Hello Marty, can you tell me about cognitive behavioral therapy?',
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      // Verify Lambda was called correctly
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:9000/api/marty/chat',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            Authorization: 'Bearer test-token',
          }),
          body: expect.stringContaining('"message":"Hello Marty, can you tell me about cognitive behavioral therapy?"'),
        })
      );

      // Verify response format
      expect(response.status).toBe(200);
      expect(responseBody).toEqual({
        response: "I'm Marty, how can I help with psychology?",
        conversation_id: 'test-conversation-123',
      });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler handles authentication errors from the Lambda function
     */
    test('handles authentication errors from Lambda', async () => {
      // Mock fetch to return an authentication error
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: jest.fn().mockResolvedValue({ error: 'Authentication error.' }),
        })
      );

      // Create a mock request with valid data
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer invalid-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: 'Hello Marty',
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(401);
      expect(responseBody).toEqual({ error: 'Authentication error.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler handles other errors from the Lambda function
     */
    test('handles other errors from Lambda', async () => {
      // Mock fetch to return a server error
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: jest.fn().mockResolvedValue({ error: 'Internal server error in chat processing.' }),
        })
      );

      // Create a mock request with valid data
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: 'Hello Marty',
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(500);
      expect(responseBody).toEqual({ error: 'Internal server error in chat processing.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the POST handler handles rate limiting
     */
    test('handles rate limiting', async () => {
      // Set up request
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: 'Hello Marty',
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      // Simulate exceeding rate limit by pre-populating request counts
      const ip = `127.0.0.${testIpCounter}`;
      const now = Date.now();
      const requestCountsExport = require('@/app/api/v1/marty/route').requestCounts;

      if (requestCountsExport) {
        requestCountsExport.set(ip, Array(21).fill(now)); // 21 requests in current minute (over limit of 20)
      } else {
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
     * Test that the POST handler handles unexpected errors
     */
    test('handles unexpected errors', async () => {
      // Mock fetch to throw an exception
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      // Create a mock request with valid data
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockResolvedValue({
          message: 'Hello Marty',
          user_id: 'test-user-123',
          conversation_history: [],
        }),
      };

      const response = await POST(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(500);
      expect(responseBody).toEqual({ error: 'Internal server error.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(console.error).toHaveBeenCalledWith('Error processing request:', expect.any(Error));
    });

    /**
     * Test that the POST handler handles JSON parsing errors
     */
    test('handles JSON parsing errors', async () => {
      // Create a mock request with JSON parsing error
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
        json: jest.fn().mockRejectedValue(new Error('Invalid JSON')),
      };

      const response = await POST(mockRequest);

      expect(response.status).toBe(500);
      expect(response.body).toEqual({ error: 'Internal server error.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });
  });

  /**
   * Tests for the GET handler (health check)
   */
  describe('GET handler', () => {
    /**
     * Test that the GET handler requires authentication
     */
    test('requires authentication', async () => {
      // Create a mock request with no authorization header
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            return null; // No authorization header
          }),
        },
      };

      const response = await GET(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(401);
      expect(responseBody).toEqual({ error: 'Authentication required.' });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the GET handler successfully returns health status
     */
    test('successfully returns health status', async () => {
      // Mock successful Lambda health check
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: jest.fn().mockResolvedValue({ status: 'healthy' }),
        })
      );

      // Create a mock request with valid authorization
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
      };

      const response = await GET(mockRequest);
      const responseBody = await response.json();

      // Verify health check was called
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:9000/api/marty/health',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );

      // Verify response
      expect(response.status).toBe(200);
      expect(responseBody).toEqual({
        status: 'healthy',
        version: '1.0.0',
        service: 'marty-chat',
      });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the GET handler handles Lambda health check failures
     */
    test('handles Lambda health check failures', async () => {
      // Mock failed Lambda health check
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          status: 503,
          json: jest.fn().mockResolvedValue({ status: 'unhealthy' }),
        })
      );

      // Create a mock request with valid authorization
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
      };

      const response = await GET(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(503);
      expect(responseBody).toEqual({
        status: 'unhealthy',
        error: 'Service is currently unavailable.',
      });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    /**
     * Test that the GET handler handles unexpected errors
     */
    test('handles unexpected errors', async () => {
      // Mock fetch to throw an exception
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      // Create a mock request with valid authorization
      const mockRequest = {
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-forwarded-for') return `127.0.0.${testIpCounter}`;
            if (header === 'authorization') return 'Bearer test-token';
            return null;
          }),
        },
      };

      const response = await GET(mockRequest);
      const responseBody = await response.json();

      expect(response.status).toBe(503);
      expect(responseBody).toEqual({
        status: 'unhealthy',
        error: 'Service is currently unavailable.',
      });
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(console.error).toHaveBeenCalledWith('Health Check Error:', expect.any(Error));
    });
  });
});
