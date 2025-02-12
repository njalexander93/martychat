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
import Link from "next/link";
import AuthenticationForm from "../../components/authentication_layout";

/**
 * Login page component.
 *
 * @returns {React.Element} The rendered login page component.
 */
export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  /**
   * Handles the login form submission.
   *
   * @param {React.FormEvent<HTMLFormElement>} e - The form submission event.
   */
  const handleLogin = async (e) => {
    e.preventDefault();

    // Validate that the user put in an email and password, and didn't just leave them blank
    if (!email || !password) {
      setLoginError("Email and password are required.");
      return;
    }

    // TODO: Add logic for sanitizing and submitting the form data to AWS Cognito
    console.log("Logging in with", { email, password });
    // You can add API call to authenticate the user
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
          />
        </div>
        {loginError && <p className="mt-1 text-sm text-red-600">{loginError}</p>}
        <button type="submit" className="w-full py-2 px-4 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 submit-button">
          Sign In
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
