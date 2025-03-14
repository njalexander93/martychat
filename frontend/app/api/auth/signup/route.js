/**
 * @fileoverview Signup API endpoint for the MartyChat application.
 * This file defines the API endpoint for user signup.
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
const requestCounts = new Map();
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
 * OPTIONS handler for the signup API endpoint.
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
 * POST handler for the signup API endpoint.
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

    // Parse the request body for the signup data
    let body;
    let email, password, firstName, lastName, organization;
    try {
      body = await request.json();

      email = body.email;
      password = body.password;
      firstName = body.firstName;
      lastName = body.lastName;
      organization = body.organization;
    } catch (jsonError) {
      return NextResponse.json({ error: 'Invalid request format.' }, { status: 400, headers: CORS_HEADERS });
    }

    // Validate required fields
    if (!email || !password || !firstName || !lastName) {
      return NextResponse.json(
        { error: 'All required fields must be filled.' },
        { status: 400, headers: CORS_HEADERS }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json({ error: 'Invalid email format.' }, { status: 400, headers: CORS_HEADERS });
    }

    // In a test environment, return a mock success response
    if (process.env.NODE_ENV === 'test') {
      return NextResponse.json(
        { message: 'User created successfully!', user: 'test-user-id' },
        { status: 200, headers: CORS_HEADERS }
      );
    }

    // Create a new user in Cognito and DynamoDB with the create-user Lambda function.
    const lambdaUrl = `${process.env.NEXT_PUBLIC_LAMBDA_URL}/api/auth/signup`;
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
      body: JSON.stringify({
        email,
        password,
        firstName,
        lastName,
        organization,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle authentication error when accessing the create-user Lambda function
      if (response.status === 403) {
        console.error('Authentication Error:', data.message);
        return NextResponse.json({ error: 'Authentication error.' }, { status: 403, headers: CORS_HEADERS });
      }
      // Handle error when the user has previously existed and the password has been associated with the account.
      else if (data.error && data.error.includes('Password has previously been used')) {
        return NextResponse.json(
          {
            error: 'This password has been previously used for an account with this email address.',
          },
          { status: response.status, headers: CORS_HEADERS }
        );
      }

      return NextResponse.json(
        { error: data.error || 'Failed to sign up.' },
        { status: response.status, headers: CORS_HEADERS }
      );
    }

    // Return response from successful create-user Lambda function
    return NextResponse.json(data, { status: 200, headers: CORS_HEADERS });
  } catch (e) {
    console.error('Signup Error:', e);
    return NextResponse.json({ error: 'Internal server error.' }, { status: 500, headers: CORS_HEADERS });
  }
}
