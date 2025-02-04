"use client";  // Required for using useEffect in the Next.js App Router

import './index.css';

import { useEffect, useState } from "react";
import Link from "next/link";

export default function Home() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Determine the correct API URL based on hostname
    const apiUrl =
      typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "http://0.0.0.0:8000";

    fetch(apiUrl)
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error("Error fetching data:", err));
  }, []);

  return (
    <div className="h-screen bg-gradient-to-r from-gray-700 to-gray-300 flex items-center justify-center">
        <div id="content" className="p-4">
            {/* TODO: Make the logo a link back to the front page. */}
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
        {/* DEBUG DEBUG DEBUG */}
        <div className="absolute bottom-4 right-4 bg-black bg-opacity-50 text-white p-2 rounded">
            <p>Backend Status: {message}</p>
        </div>
        {/* DEBUG DEBUG DEBUG */}
    </div>
  );
}
