/**
 * @fileoverview Chat Interface for the user to interact with the Marty chatbot.
 * This file contains the main logic for the marty chat interface.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

"use client";

import { useEffect, useState } from "react";
import ChatInterface from "@/components/ChatInterface";
import { martyConfig } from "@/chatbots/marty";

/**
 * The Marty chat interface component.
 *
 * @returns {React.Element} The rendered signup page component.
 */
export default function MartyPage() {
  useEffect(() => {
    // Set a unique user ID for the session. This is used to identify the user across multiple sessions. If the user ID
    // is not set, generate a new one.
    const userId = window.sessionStorage.getItem("userId");
    if (!userId) {
      window.sessionStorage.setItem("userId", `user_${Date.now().toString()}`);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8 font-roboto-slab">Welcome to MartyChat</h1>
        <ChatInterface {...martyConfig} />
      </div>
    </div>
  )
}
