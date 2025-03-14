/**
 * @fileoverview Middleware for MartyChat frontend.
 * This middleware is used to protect routes that require authentication.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-28
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/** Middleware function to protect routes that require authentication.
 *
 * @param {NextRequest} request The incoming request object
 */
export function middleware(request: NextRequest) {
  // Get the pathname from the URL
  const path = request.nextUrl.pathname;

  // Define public paths that don't require authentication
  const publicPaths = ['/login', '/signup', '/'];
  const isPublicPath = publicPaths.includes(path);

  // Get the token from cookies
  const idToken = request.cookies.get('idToken')?.value;

  // If user is authenticated redirect them to the marty chat page
  if (idToken && isPublicPath) {
    return NextResponse.redirect(new URL('/marty', request.url));
  }

  // If user is not authenticated and tries to access protected routes,
  // redirect them to login
  if (!idToken && !isPublicPath) {
    const loginUrl = new URL('/login', request.url);
    // Store the attempted URL to redirect back after login
    loginUrl.searchParams.set('callbackUrl', path);
    return NextResponse.redirect(loginUrl);
  }

  // Allow the request to continue
  return NextResponse.next();
}

// Configure which routes middleware will run on
export const config = {
  // Match all routes except for:
  // - api routes (/api/*)
  // - static files (_next/static/*)
  // - public files (favicon.ico, etc.)
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|icon.ico|assets).*)'],
};
