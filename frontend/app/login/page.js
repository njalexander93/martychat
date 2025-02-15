/**
 * @fileoverview Login page component for the MartyChat application.
 * This file defines the login page, including form handling and validation.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-04
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

"use client";  // Required for using useEffect in the Next.js App Router

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthenticationForm from "../../components/authentication_layout";
import sanitizeHtml from "sanitize-html";

/**
 * Login page component.
 *
 * @returns {React.Element} The rendered login page component.
 */
export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Use the Next.js router to redirect the user to the chat page after login
  const router = useRouter();

  /**
   * Handles the login form submission.
   *
   * @param {React.FormEvent<HTMLFormElement>} e - The form submission event.
   */
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError("");
    setIsLoading(true); // Set loading state to true. This will be used to show a loading spinner

    // Sanitize the email input to prevent XSS attacks
    const sanitizedEmail = sanitizeHtml(email);

    // Create an object to hold the form data
    const loginData = {
      email: sanitizedEmail,
      password: password,
    };


    // Validate that the user put in an email and password, and didn't just leave them blank
    if (!email || !password) {
      setIsLoading(false);
      setLoginError("Email and password are required.");
      return;
    }

    try {
      // Create a new user in Cognito and DynamoDB with the create-user Lambda function.
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(loginData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to login.');
      }

      // Store the authentication tokens in local storage
      if (data.authenticationResult) {
        // Store the tokens in local storage
        localStorage.setItem("idToken", data.authenticationResult.idToken); // ID token for authentication
        localStorage.setItem("accessToken", data.authenticationResult.accessToken); // Access token for API requests
        localStorage.setItem("refreshToken", data.authenticationResult.refreshToken); // Refresh token for refreshing the ID token

        // Set the ID token in a cookie for middleware authentication.
        document.cookie = `idToken=${data.authenticationResult.idToken}; path=/`;

        // Get the callback URL if it exists
        const urlParams = new URLSearchParams(window.location.search);
        const callbackUrl = urlParams.get("callbackUrl") || "/marty";

        console.log("Login successful! Redirecting to:", callbackUrl);

        // Clear the form fields
        setIsLoading(false);
        setLoginError("");

        // Redirect to the chat page
        await router.push(callbackUrl); // Redirect to the chat page
      }
    }
    catch (e) {
      console.error("Error logging in:", e);
      setIsLoading(false);
      setLoginError("Sign in failed. Please try again later.");
    }
    finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthenticationForm>
      <h1 className="text-2xl font-bold mb-6 text-center text-gray-300">Sign In</h1>
      <form onSubmit={handleLogin}>
        <div className="mb-4">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="mt-1 p-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 sm:text-sm"
            disabled={isLoading}
          />
        </div>
        <div className="mb-6">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="mt-1 p-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 sm:text-sm"
            disabled={isLoading}
          />
        </div>
        <div className="mb-4 text-center">
          {loginError && <p className="mb-2 text-sm text-red-600">{loginError}</p>} {/* Display the signup error message */}
        </div>
        <button
          type="submit"
          className={`w-full py-2 px-4 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 submit-button ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          disabled={isLoading}
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </button>
        <div className="text-center mt-4">
          <Link href="/signup" className="text-sm">
            Create an account
          </Link>
        </div>
      </form>
    </AuthenticationForm>
  );
}
