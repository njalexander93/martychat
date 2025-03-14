/**
 * @fileoverview Login API endpoint for the MartyChat application.
 * This file defines the API endpoint for user login functionality.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-28
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import { NextResponse } from 'next/server';

const RATE_LIMIT_DURATION = 60 * 1000; // 1 minute
const MAX_REQUESTS = 5; // 5 requests
let requestCounts = new Map();
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': process.env.NODE_ENV === 'production' ? 'https://www.martychat.com' : '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
};

/** Rate limiting middleware for the signup API endpoint.
 *
 * @param {String} ip The IP address of the incoming request
 * @returns {Boolean} True if the IP address is rate limited, false otherwise.
 */
function isRateLimited(ip) {
  // Disable rate limiting in development and testing environments
  if (process.env.NODE_ENV !== 'production') {
    return false;
  }

  const now = Date.now();
  const count = requestCounts.get(ip) || [];

  // Clean up old requests
  const recentRequests = count.filter((time) => time > now - RATE_LIMIT_DURATION);

  // Check if rate limit is exceeded
  if (recentRequests.length > MAX_REQUESTS) {
    return true;
  }

  // Update the request counts
  recentRequests.push(now);
  requestCounts.set(ip, recentRequests);
  return false;
}

/**
 * OPTIONS handler for the login API endpoint.
 *
 * @returns {NextResponse} The response object.
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: CORS_HEADERS,
  });
}

/**
 * POST handler for the login API endpoint.
 *
 * @param {Request} request The incoming request object.
 * @returns {NextResponse} The response object.
 */
export async function POST(request) {
  try {
    // Check the rate limit
    const ip = request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || 'unknown';
    if (isRateLimited(ip)) {
      return NextResponse.json(
        { error: 'Rate limit exceeded. Please try again later.' },
        { status: 429, headers: CORS_HEADERS }
      );
    }

    // Parse the request body for email
    let body;
    try {
      body = await request.json();
    } catch (jsonError) {
      return NextResponse.json({ error: 'Invalid JSON format.' }, { status: 400, headers: CORS_HEADERS });
    }

    const { email, password } = body;

    // If neither is provided, throw an error
    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password are required.' }, { status: 400, headers: CORS_HEADERS });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json({ error: 'Invalid email format.' }, { status: 400, headers: CORS_HEADERS });
    }

    // Login the user to Cognito with the login Lambda function
    const lambdaUrl = `${process.env.NEXT_PUBLIC_LAMBDA_URL}/api/auth/login`;
    console.log('Calling login Lambda function:', lambdaUrl);
    const response = await fetch(lambdaUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: '*/*',
        'User-Agent': 'MartyChat/1.0',
        ...(process.env.NODE_ENV === 'production' &&
          {
            // TODO: Add production-specific headers to call remote lambda functions
          }),
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 403) {
        console.error('Authentication Error:', data.message);
        return NextResponse.json({ error: 'Authentication error.' }, { status: 403, headers: CORS_HEADERS });
      }
      return NextResponse.json(
        { error: data.error || 'Failed to login.' },
        { status: response.status, headers: CORS_HEADERS }
      );
    }

    // Return a success response
    return NextResponse.json({ message: 'Login successful' }, { status: 200, headers: CORS_HEADERS });
  } catch (e) {
    console.log('DEBUG: Login error:', e);
    console.error('Login error:', e);
    return NextResponse.json({ error: 'Failed to login.' }, { status: 500, headers: CORS_HEADERS });
  }
}
