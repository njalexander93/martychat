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

import { useState } from "react";

export default function MartyChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch the API URL from the environment variables
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const sendMessage = async () => {
    if (!input.trim()) return;

    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input, user_id: "anonymous" }),
      });

      if (!response.ok) throw new Error("Failed to fetch response");

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);

    } catch (err) {
      console.error("Error:", err);
      setError("Server error. Try again later.");
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <div className="chat-container">
      {/* Chat UI Code */}
    </div>
  );
}
