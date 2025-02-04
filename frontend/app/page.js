/**
 * @fileoverview Home page component for the MartyChat application.
 * This file defines the home page, including links to login and signup pages.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

"use client";  // Required for using useEffect in the Next.js App Router

import './index.css';

import { useEffect, useState } from "react";
import Link from "next/link";

/**
 * Home page component.
 *
 * @returns {React.Element} The rendered home page component.
 */
export default function Home() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Determine the correct API URL based on hostname
    const apiUrl =
      typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "http://0.0.0.0:8000";

    // Fetch the backend status message
    fetch(apiUrl)
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error("Error fetching data:", err));
  }, []);

  return (
    <div className="h-screen bg-gradient-to-r from-gray-700 to-gray-300 flex items-center justify-center">
        <div id="content" className="p-4">
            <img src="/assets/MartyChat_Full-833x200.png" alt="MartyChat Logo" className="unselectable"/>
            <div className="mt-4 space-x-10 flex items-center justify-center">
              <Link id="link-login" href="/login" className="inline-block link" style={{ fontFamily: 'var(--font-roboto-slab)'}}>
                Sign In
              </Link>
              <Link id="link-signup" href="/signup" className="inline-block link" style={{ fontFamily: 'var(--font-roboto-slab)'}}>
                Sign Up
              </Link>
            </div>
        </div>
    </div>
  );
}
