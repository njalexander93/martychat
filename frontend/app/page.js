/**
 * @fileoverview Home page component for the MartyChat application.
 * This file defines the home page, including links to login and signup pages.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-04
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

'use client'; // Required for using useEffect in the Next.js App Router

import '@/styles/index.css';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

/**
 * Home page component.
 *
 * @returns {React.Element} The rendered home page component.
 */
export default function Home() {
  const [message, setMessage] = useState('');
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!apiUrl) {
          console.warn('API_URL not configured');
          setBackendStatus('disconnected');
          return;
        }

        const response = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          setMessage(data.message);
          setBackendStatus('connected');
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      } catch (error) {
        console.error('Backend connection error:', error);
        setBackendStatus('disconnected');

        // In development, show a more helpful message
        if (process.env.NODE_ENV === 'development') {
          setMessage('Backend not connected. Make sure your FastAPI server is running on localhost:8000');
        } else {
          setMessage('Welcome to MartyChat');
        }
      }
    };

    checkBackend();
  }, []);

  return (
    <div className="h-screen bg-gradient-to-l from-bg-secondary from-20% to-bg-dark to-100% flex items-center justify-center">
      <div id="content" className="p-4">
        <Image
          src="https://martychat-assets-png.s3.amazonaws.com/MartyChat_Full-833x200.png"
          alt="MartyChat Logo"
          width={833}
          height={200}
          className="unselectable"
          priority
        />
        <div className="mt-4 space-x-10 flex items-center justify-center">
          <Link
            id="link-login"
            href="/login"
            className="inline-block link"
            style={{ fontFamily: 'var(--font-roboto-slab)' }}
          >
            Sign In
          </Link>
          <Link
            id="link-signup"
            href="/signup"
            className="inline-block link"
            style={{ fontFamily: 'var(--font-roboto-slab)' }}
          >
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
}
