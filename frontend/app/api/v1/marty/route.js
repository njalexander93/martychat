/**
 * @fileoverview Marty chat API endpoint for the MartyChat application.
 * This file defines the API endpoint for the Marty chatbot interactions.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

const RATE_LIMIT_DURATION = 60 * 1000; // 1 minute
const MAX_REQUESTS = 20; // 20 requests
const requestCounts = new Map();
const CORS_HEADERS = {
    "Access-Control-Allow-Origin": process.env.NODE_ENV === 'production'
        ? "https://www.martychat.com"
        : "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS, GET",
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
    });
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

        // Verify authentication token
        const token = request.headers.get("authorization");
        if (!token || !token.startsWith("Bearer ")) {
            return new Response(JSON.stringify({ error: "Authentication required." }), {
                status: 401,
                headers: {
                    ...CORS_HEADERS,
                    "Content-Type": "application/json",
                }
            });
        }

        // Parse the request body for the user message and conversation history
        const { message, conversation_history, user_id } = await request.json();

        // Validate required fields
        if (!user_id) {
            return new Response(JSON.stringify({ error: "User ID is required." }), {
                status: 400,
                headers: CORS_HEADERS
            });
        }
        if (!message){
            return new Response(JSON.stringify({ error: "Message is required." }), {
                status: 400,
                headers: CORS_HEADERS
            });
        }
        else if (typeof message !== "string") {
            return new Response(JSON.stringify({ error: "Message is of the wrong data type." }), {
                status: 400,
                headers: CORS_HEADERS
            });
        }

        const lambdaUrl = `${process.env.NEXT_PUBLIC_LAMBDA_URL}/api/marty/chat`;
        const response = await fetch(lambdaUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": token,
                "Accept": "*/*",
                "User-Agent": "MartyChat/1.0",
                ...(process.env.NODE_ENV === 'production' && {
                    // TODO: Add production-specific headers
                })
            },
            body: JSON.stringify({
                message,
                user_id,
                conversation_history: conversation_history || [],
                timestamp: new Date().toISOString()
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                console.error("Authentication Error:", data.message);
                return new Response(JSON.stringify({ error: "Authentication error." }), {
                    status: response.status,
                    headers: CORS_HEADERS
                });
            }

            // Handle other errors
            return new Response(JSON.stringify({ error: data.error || "Failed to process chat message." }), {
                status: response.status,
                headers: CORS_HEADERS
            });
        }

        // Return successful response
        return new Response(JSON.stringify({
            response: data.response,
            conversation_id: data.conversation_id
        }), {
            status: 200,
            headers: {
                ...CORS_HEADERS,
                "Content-Type": "application/json"
            }
        });
    }
    catch (e) {
        console.error("Error processing request:", e);
        return new Response(JSON.stringify({ error: "Internal server error." }), {
            status: 500,
            headers: CORS_HEADERS
        });
    }
}

/**
 * GET handler for checking Marty service health.
 *
 * @param {Request} request The incoming request object
 * @returns {Response} The response object
 */
export async function GET(request) {
    try {
        // Verify authentication
        const authHeader = request.headers.get('authorization');
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return new Response(JSON.stringify({ error: "Authentication required." }), {
                status: 401,
                headers: CORS_HEADERS
            });
        }

        // Check Lambda health
        const healthUrl = `${process.env.NEXT_PUBLIC_LAMBDA_URL}/api/marty/health`;
        const response = await fetch(healthUrl, {
            method: "GET",
            headers: {
                "Authorization": authHeader,
                "Accept": "*/*",
                "User-Agent": "MartyChat/1.0"
            }
        });

        if (!response.ok) {
            throw new Error('Lambda health check failed');
        }

        return new Response(JSON.stringify({
            status: 'healthy',
            version: '1.0.0',
            service: 'marty-chat'
        }), {
            status: 200,
            headers: {
                ...CORS_HEADERS,
                "Content-Type": "application/json"
            }
        });
    }
    catch (e) {
        console.error("Health Check Error:", e);
        return new Response(JSON.stringify({
            status: 'unhealthy',
            error: "Service is currently unavailable."
        }), {
            status: 503,
            headers: CORS_HEADERS
        });
    }
}
