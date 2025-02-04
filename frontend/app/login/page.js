"use client";  // Required for using useEffect in the Next.js App Router

import { useState } from "react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    // Handle login logic here
    console.log("Logging in with", { username, password });
    // You can add API call to authenticate the user
  };

  return (
    <div className="h-screen bg-gradient-to-r from-gray-700 to-gray-300 flex items-center justify-center">

    </div>
  );
}
