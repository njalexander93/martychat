/**
 * @fileoverview Login API endpoint for the MartyChat application.
 * This file defines the API endpoint for user login functionality.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

const RATE_LIMIT_DURATION = 60 * 1000; // 1 minute
const MAX_REQUESTS = 5; // 5 requests
const requestCounts = new Map();
const CORS_HEADERS = {
    "Access-Control-Allow-Origin": process.env.NODE_ENV === 'production'
        ? "https://www.martychat.com"
        : "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400"
}

/** Rate limiting middleware for the signup API endpoint.
 *
 * @param {String} ip The IP address of the incoming
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
 * OPTIONS handler for the login API endpoint.
 *
 * @param {Request} request The incoming request object.
 * @returns {Response} The response object.
 */
export async function OPTIONS(request) {
    return new Response(null, {
        status: 204,
        headers: CORS_HEADERS
    })
}

/**
 * POST handler for the login API endpoint.
 *
 * @param {Request} request The incoming request object.
 * @returns {Response} The response object.
 */
export async function POST(request) {
    try {
        // Check the rate limit
        const ip = request.headers.get("CF-Connecting-IP") || request.headers.get("X-Forwarded-For") || "unknown";
        if (isRateLimited(ip)) {
            return new Response(JSON.stringify({ error: "Rate limit exceeded. Please try again later." }), {
                status: 429,
                headers: {
                    ...CORS_HEADERS,
                    "Content-Type": "application/json",
                }
            });
        }

        // Parse the request body for the signup data
        const { email, password } = await request.json();

        // Validate that the user put in an email and password.
        if (!email || !password) {
            return new Response(JSON.stringify({ error: "Email and password are required." }), {
                status: 400,
                headers: CORS_HEADERS
            });
        }

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return new Response(JSON.stringify({ error: "Invalid email." }), {
                status: 400,
                headers: CORS_HEADERS
            });
        }

        // Login the user to Cognito with the login Lambda function
        const lambdaUrl = `${process.env.NEXT_PUBLIC_LAMBDA_URL}/api/auth/login`;
        console.log("Calling login Lambda function:", lambdaUrl);
        const response = await fetch(lambdaUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "MartyChat/1.0",
                ...(process.env.NODE_ENV === 'production' && {
                    // TODO: Add production-specific headers to call remote lambda functions
                })
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            if (response.status === 403) {
                console.error("Authentication Error:", data.message);
                return new Response(JSON.stringify({ error: "Authentication error." }), {
                    status: 403,
                    headers: CORS_HEADERS
                });
            }
            return new Response(JSON.stringify({ error: data.error || "Failed to login." }), {
                status: response.status,
                headers: CORS_HEADERS
              });
        }

        // Return response from successful create-user Lambda function
        return new Response(JSON.stringify(data), {
            status: 200,
            headers: {
                ...CORS_HEADERS,
                "Content-Type": "application/json"
            }
          });
    }
    catch (e) {
        console.error("Signup Error:", e)
        return new Response(JSON.stringify({ error: "Internal server error." }), {
            status: 500,
            headers: CORS_HEADERS
          });
    }
}
