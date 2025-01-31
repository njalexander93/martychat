"use client";  // Required for using useEffect in the Next.js App Router

import { useEffect, useState } from "react";

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
        <div>
            <h1>Next.js + FastAPI Chatbot</h1>
            <p>Backend says: {message}</p>
        </div>
    );
}
