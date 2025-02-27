/**
 * @fileoverview Chat interface template for the MartyChat application.
 * This file defines the layout for the chat interface.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import React, { useState, useRef, useEffect } from "react";
import { Menu, X } from "lucide-react";
import { isAuthenticated, checkAndRefreshAuth, handleLogout } from "@/utils/auth";

/**
 * The chat interface component for the MartyChat application.
 *
 * @returns {React.Element} The rendered signup page component.
 */
const ChatInterface = ({
    title,
    endpoint,
    placeholder = "Type your message...",
    welcomeMessage = null,
    maxInputLines = 18,
    theme = {
        userMessage: 'bg-primary text-text-light',
        botMessage: 'bg-bg-secondary text-text-primary',
        fonts: {
            title: 'font-roboto-slab',
            messages: 'font-roboto',
            input: 'font-roboto-flex'
        },
        container: {
            background: 'bg-transparent border-transparent',
            input: 'bg-transparent border-transparent'
        }
    }
}) => {
    // State for managing messages. The role property determines if the message is from the user or the chatbot.
    const [messages, setMessages] = useState(
        welcomeMessage ? [{ role: "chatbot", content: welcomeMessage }] : []
    );
    const [input, setInput] = useState(""); // State for user input
    const [loading, setLoading] = useState(false); // State for loading indicator
    const [isAuthed, setisAuthed] = useState(false); // State for user authentication
    const textareaRef = useRef(null); // Ref for textarea to auto-resize
    const chatContainerRef = useRef(null); // Ref for chat container to auto-scroll
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const menuRef = useRef(null); // Ref for menu to close on outside click
    const [isSidebarOpen, setIsSidebarOpen] = useState(false); // State for sidebar menu

    // Check if the user is authenticated and refresh tokens if necessary.
    useEffect(() => {
        const checkAuth = async () => {
            if (!isAuthenticated()) {
                handleLogout(window.location.pathname);
                return;
            }
            setisAuthed(true);
        };

        checkAuth();

        // Set up periodic checks
        const interval = setInterval(async () => {
            await checkAndRefreshAuth();
        }, 4 * 60 * 1000); // Check every 4 minutes

        return () => clearInterval(interval);
    }, []);

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsMenuOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Auto-resize textarea as user types
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto"; // Reset height to auto
            const scrollHeight = textareaRef.current.scrollHeight; // Height of the scrollable content
            const lineHeight = 16; // Line height in pixels
            const maxHeight = lineHeight * maxInputLines; // Maximum height of the textarea
            textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + "px"; // Set the height to the minimum of scrollHeight and maxHeight
        }
    }, [input, maxInputLines]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight; // Scroll to the bottom of the chat container
        }
    }, [messages]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    /**
     * Compresses the chat history for a maximum number of messages for performance.
     *
     * @param {Array} history - The array of conversation history.
     * @param {number} maxInteractions - The maximum number of interactions to store.
     * @returns {Array} The compressed conversation history.
     */
    const compressHistory = (history, maxInteractions) => {
        const maxHistory = maxInteractions * 2; // Include both user and response messages

        // Remove the welcome message from the chat history and compress to the maximum number of interactions.
        const filteredHistory = history.filter(message => message.role !== "chatbot" || message.content !== welcomeMessage);
        if (filteredHistory.length === 0) {
            return [];
        }
        if (filteredHistory.length <= maxHistory) {
            return filteredHistory;
        }
        else {
            return filteredHistory.slice(-maxHistory);
        }
    }

    /**
     * Handles the submission of the user message to the chatbot.
     *
     * @param {React.FormEvent<HTMLFormElement>} e - The form submission event.
     */
    const handleSubmit = async (e) => {
        e.preventDefault(); // Prevent default form submission behavior

        // If the input is empty or only whitespace, return early so that no message is sent.
        if (!input.trim()) return;

        // Format the user message to prepare for sending.
        const userMessage = input.trim();
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]); // Add user message to messages state
        setLoading(true);
        setInput(""); // Clear the input field

        try {
            // Check and refresh authentication before making request
            const isAuthed = await checkAndRefreshAuth();
            if (!isAuthed) {
                return;
            }

            const history = compressHistory(messages, 3); // Compress the chat history to store only the last 3 interactions

            const backendUrl = process.env.NEXT_PUBLIC_API_URL + endpoint;
            const response = await fetch(backendUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + localStorage.getItem("idToken"),
                },
                body: JSON.stringify({
                    message: userMessage, // Include the user message in the request
                    conversation_history: history, // Include conversation history in the request
                }),
            });

            if (!response.ok) {
                // If the user is not authorized, redirect to the login page.
                // if (response.status === 401 || response.status === 403) {
                //     window.location.href = "/login?callbackUrl=" + encodeURIComponent(window.location.pathname);
                //     return;
                // }
                throw new Error("Failed to fetch response. Status: " + response.status);
            }

            const data = await response.json(); // Parse the response data as JSON

            // Add the chatbot response to the messages state.
            setMessages((prev) => [...prev, { role: "chatbot", content: data.response }]);
        }
        catch (error) {
            console.error("Error sending message:", error);
            setMessages((prev) => [
                ...prev,
                {
                    role: "chatbot",
                    content: "Sorry, I encountered an error. Please try again.",
                },
            ]);
        }
        finally {
            setLoading(false); // Set loading state to false
        }
    };

    const handleLogoutClick = (e) => {
        e.preventDefault();
        handleLogout("/");
    };

    if (!isAuthed) {
        return <div>Loading...</div>;
    }

    return (
        <div className="relative h-screen bg-gradient-to-l from-bg-secondary from-20% to-bg-dark to-100%">
            {/* Header with Hamburger */}
            <div className="p-4 px-8 flex justify-between items-center">
                <button
                    onClick={() => setIsSidebarOpen(true)}
                    className="p-1 text-primary rounded-md border border-primary hover:text-primary-hover hover:bg-white/5 hover:border-primary-hover active:text-primary-active active:border-primary-active transition-colors"
                >
                    <Menu size={24} />
                </button>
                <img
                    src="/assets/MartyChat_Full-833x200.png"
                    alt="MartyChat Logo"
                    className="w-60 select-none"
                />
            </div>

            {/* Overlay Sidebar */}
            <div
                className={`fixed inset-0 bg-black transition-opacity duration-300 z-40 ${
                    isSidebarOpen ? 'opacity-50' : 'opacity-0 pointer-events-none'
                }`}
                onClick={() => setIsSidebarOpen(false)}
            />
            {/* Sidebar - slide in/out */}
            <div
                className={`fixed inset-y-0 left-0 w-64 bg-bg-dark border-r border-gray-500 border-opacity-20 p-4 z-50 shadow-lg transition-transform duration-300 ${
                    isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            >
                <div className="flex justify-end mb-4">
                    <button
                        onClick={() => setIsSidebarOpen(false)}
                        className="p-0.25 rounded-md border border-text-text-light text-text-light hover:bg-white/5 hover:text-primary hover:border-primary active:text-primary-active active:border-primary-active transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>
                <div className="flex flex-col gap-2">
                    {/* TODO: Add link to profile page after creation. */}
                    <a href="#" className="p-3 text-text-light hover:bg-white/5 rounded-lg transition-colors">
                        Profile
                    </a>
                    <a href="#" onClick={handleLogoutClick} className="p-3 text-text-light hover:bg-white/5 rounded-lg transition-colors">
                        Logout
                    </a>
                </div>
            </div>

            {/* Chat Messages Container - Add bottom padding to account for fixed input form */}
            <div
                ref={chatContainerRef}
                className={`h-[calc(100vh-140px)] overflow-y-auto px-4 pb-20 space-y-4 ${theme.fonts.messages}
                [&::-webkit-scrollbar]:w-2
                [&::-webkit-scrollbar-track]:bg-transparent
                [&::-webkit-scrollbar-thumb]:rounded-full
                [&::-webkit-scrollbar-thumb]:bg-bg-primary
                [&::-webkit-scrollbar-thumb:hover]:bg-text-light
                [&::-webkit-scrollbar-button]:hidden`}
            >
                <div className="max-w-4xl mx-auto space-y-4">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-lg p-3 whitespace-pre-wrap break-words ${
                                    message.role === 'user'
                                        ? theme.userMessage
                                        : theme.botMessage
                                }`}
                            >
                                {message.content}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-gray-200 text-gray-800 rounded-lg p-3">
                                Thinking...
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Input Form */}
            <div className="fixed bottom-0 left-0 right-0 p-3 bg-opacity-5">
    <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit}>
            <div className="relative flex flex-col bg-bg-input -ml-4 bg-opacity-10 rounded-xl border border-gray-500 border-opacity-20 shadow-lg overflow-hidden">
                <div className="relative flex">
                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={placeholder}
                        className={`flex-1 min-h-[44px] max-h-[${maxInputLines * 16}px] p-3 pr-24 bg-transparent border-none resize-none focus:outline-none focus:ring-0 ${theme.fonts.input}`}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                    />
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className={`absolute top-1 right-1 p-2 rounded-lg bg-primary text-white hover:bg-primary-hover active:bg-primary-active disabled:bg-bg-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${theme.fonts.input}`}
                    >
                        Send
                    </button>
                </div>
                <div className="px-3 pb-1.5 text-text-secondary text-[11px]">
                <span className="bg-bg-secondary bg-opacity-20 px-1.5 py-1
                 text-[10px] rounded-md"><code>Shift + Return</code></span> for new line
                </div>
            </div>
        </form>
    </div>
</div>
        </div>
    )
};

export default ChatInterface;
