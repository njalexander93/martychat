/**
 * @fileoverview Refresh API endpoint for the MartyChat application.
 * This file defines the API endpoint for token refresh functionality.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import { NextResponse } from 'next/server';

const RATE_LIMIT_DURATION = 60 * 1000; // 1 minute
const MAX_REQUESTS = 10; // 10 requests (higher than login since refreshes are more frequent)
const requestCounts = new Map();
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': process.env.NODE_ENV === 'production' ? 'https://www.martychat.com' : '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
  'Content-Type': 'application/json',
};

/** Rate limiting middleware for the refresh API endpoint.
 *
 * @param {String} ip The IP address of the incoming request
 * @returns {Boolean} True if the IP address is rate limited, false otherwise.
 */
function isRateLimited(ip) {
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
 * POST handler for the refresh API endpoint.
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

    // Parse the request body
    let body;
    try {
      body = await request.json();
    } catch (jsonError) {
      return NextResponse.json({ error: 'Invalid JSON format.' }, { status: 400, headers: CORS_HEADERS });
    }

    const { refreshToken, userId } = body;

    // Validate refresh token presence
    if (!refreshToken) {
      return NextResponse.json({ error: 'Refresh token is required.' }, { status: 400, headers: CORS_HEADERS });
    }

    // Validate userId presence
    if (!userId) {
      return NextResponse.json({ error: 'User ID is required.' }, { status: 400, headers: CORS_HEADERS });
    }

    // Call the refresh Lambda function
    const lambdaUrl = `${process.env.NEXT_PUBLIC_LAMBDA_URL}/api/auth/refresh`;
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
      body: JSON.stringify({ refreshToken, userId }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || 'Failed to refresh token.' },
        { status: response.status, headers: CORS_HEADERS }
      );
    }

    return NextResponse.json(data, {
      status: 200,
      headers: CORS_HEADERS,
    });
  } catch (e) {
    console.error('Refresh Error:', e);
    return NextResponse.json({ error: 'Internal server error.' }, { status: 500, headers: CORS_HEADERS });
  }
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
