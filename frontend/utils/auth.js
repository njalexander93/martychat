/**
 * @fileoverview Authentication utilities for the MartyChat application.
 * This file provides centralized authentication handling functions.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-28
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

/**
 * Check if access token is expired or about to expire (within 5 minutes)
 * @returns {boolean}
 */
export const isTokenExpired = () => {
    const now = new Date().getTime();
    const idTokenExpires = localStorage.getItem("idTokenExpires");
    const accessTokenExpires = localStorage.getItem("accessTokenExpires");
    const refreshTokenExpires = localStorage.getItem("refreshTokenExpires");

    // If no expiration times exist, consider tokens expired
    if (!idTokenExpires || !accessTokenExpires || !refreshTokenExpires) {
        return true;
    }

    // Check if refresh token is expired
    if (now > parseInt(refreshTokenExpires)) {
        return true;
    }

    // Check if tokens are expired or about to expire (within 5 minutes)
    const fiveMinutes = 5 * 60 * 1000;
    return now > (parseInt(idTokenExpires) - fiveMinutes) ||
           now > (parseInt(accessTokenExpires) - fiveMinutes);
};

/**
 * Refresh the authentication tokens
 * @returns {Promise<boolean>} Success status of the refresh
 */
export const refreshTokens = async () => {
    try {
        const refreshToken = localStorage.getItem("refreshToken");
        const userId = window.sessionStorage.getItem("userId");
        if (!refreshToken) {
            console.error("No refresh token found");
            return false;
        }
        if (!userId) {
            console.error("No user ID found");
            return false;
        }

        const response = await fetch("/api/auth/refresh", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "MartyChat/1.0",
                ...(process.env.NODE_ENV === 'production' && {
                    // TODO: Add production-specific headers to call remote lambda functions
                })
            },
            body: JSON.stringify({ refreshToken, userId }),
        });

        if (!response.ok) {
            console.log("Failed to refresh token.");
            throw new Error("Failed to refresh token");
        }

        const data = await response.json();

        const now = new Date().getTime();

        // Update tokens and expiration times
        localStorage.setItem("idToken", data.authenticationResult.idToken);
        localStorage.setItem("accessToken", data.authenticationResult.accessToken);
        localStorage.setItem("idTokenExpires", now + ((data.authenticationResult.idTokenExpires || 3600) * 1000));
        localStorage.setItem("accessTokenExpires", now + ((data.authenticationResult.accessTokenExpires || 3600) * 1000));

        // Update cookie
        document.cookie = `idToken=${data.authenticationResult.idToken}; path=/`;

        return true;
    } catch (error) {
        console.error("Error refreshing tokens:", error);
        return false;
    }
};

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export const isAuthenticated = () => {
    const userId = window.sessionStorage.getItem("userId");
    const idToken = localStorage.getItem("idToken");
    return !!(userId && idToken);
};

/**
 * Handle user logout
 * @param {string} [redirectPath="/"] - Path to redirect to after logout
 */
export const handleLogout = (redirectPath = "/") => {
    // Clear all auth data
    window.sessionStorage.removeItem("userId");
    localStorage.removeItem("idToken");
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("idTokenExpires");
    localStorage.removeItem("accessTokenExpires");
    localStorage.removeItem("refreshTokenExpires");

    // Clear the authentication cookie
    document.cookie = "idToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

    // Redirect to login with callback URL
    const callbackUrl = encodeURIComponent(redirectPath);
    window.location.href = `/login?callbackUrl=${callbackUrl}`;
};

/**
 * Check and refresh authentication if needed
 * @returns {Promise<boolean>} Authentication status
 */
export const checkAndRefreshAuth = async () => {
    if (!isAuthenticated()) {
        handleLogout(window.location.pathname);
        return false;
    }

    if (isTokenExpired()) {
        const refreshSuccess = await refreshTokens();
        if (!refreshSuccess) {
            handleLogout(window.location.pathname);
            return false;
        }
    }

    return true;
};
