/**
 * @fileoverview Unit tests for the Login API Route in MartyChat. These tests validate CORS handling in OPTIONS requests
 * and input validation for the POST login request.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

// Set test environment
process.env.NODE_ENV = 'test';

// Import necessary modules
const { createRequest, createResponse } = require('node-mocks-http');
const { NextResponse } = require('next/server');
const { POST, OPTIONS } = require('@/app/api/auth/login/route');

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
        // ✅ Fix: Properly mock `NextResponse.json()`
        return new this(body, options);
      }
    },
  };
});

/**
 * Unit tests for the Login API Route.
 */
describe('Login API Route', () => {
  // Clear mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
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
   * Tests for the POST login request handler
   */
  describe('POST handler', () => {
    /**
     * Test that the POST handler returns a 400 error when the email is missing.
     */
    test('returns 400 when email is missing', async () => {
      // Create a mock request with only the password.
      const req = createRequest({
        method: 'POST',
        url: '/api/auth/login',
        headers: { 'Content-Type': 'application/json' },
        body: { password: 'Test1234!' }, // ✅ Mock JSON body
      });

      // Call the POST handler with the mock request.
      const response = await POST(req);

      // Validate the response status.
      expect(response.status).toBe(400);
      expect(await response.body).toEqual({ error: 'Email and password are required.' });
    });

    /**
     * Test that the POST handler returns a 400 error when the password is missing.
     */
    test('returns 400 when password is missing', async () => {
      // Create a mock request with only the email.
      const req = createRequest({
        method: 'POST',
        url: '/api/auth/login',
        headers: { 'Content-Type': 'application/json' },
        body: { email: 'test@example.com' },
      });

      // Call the POST handler with the mock request.
      const response = await POST(req);

      // Validate the response status.
      expect(response.status).toBe(400);
      expect(await response.body).toEqual({ error: 'Email and password are required.' });
    });

    /**
     * Test that the POST handler returns a 200 success message when the email and password are provided.
     */
    test('returns 200 when email and password are provided', async () => {
      // Create a mock request with the email and password.
      const req = createRequest({
        method: 'POST',
        url: '/api/auth/login',
        headers: { 'Content-Type': 'application/json' },
      });
      req.body = JSON.stringify({ email: 'test@example.com', password: 'Test1234!' });

      // Mock the request's JSON parsing function.
      req.json = async () => JSON.parse(req.body);

      // Call the POST handler with the mock request.
      const response = await POST(req);

      // Validate the response status.
      expect(response.status).toBe(200);
      expect(await response.body).toEqual({ message: 'Login successful' });
    });
  });
});
