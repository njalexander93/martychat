"use client";  // Required for using useEffect in the Next.js App Router

import './signup.css'

import { useState } from "react";
import sanitizeHtml from "sanitize-html";

export default function SignupPage() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordValid, setPasswordValid] = useState({
    length: false,
    lower: false,
    upper: false,
    number: false,
  });
  const [nameError, setNameError] = useState({ firstName: "", lastName: "" });
  const [emailError, setEmailError] = useState(""); // Initialize emailError state

  const handleSignup = async (e) => {
    e.preventDefault();
    // Handle signup logic here
    console.log("Signing up with", { firstName, lastName, email, password });
    // You can add API call to register the user
  };

  const validatePassword = (password) => {
    const length = password.length >= 8 && password.length <= 64;
    const lower = /[a-z]/.test(password);
    const upper = /[A-Z]/.test(password);
    const number = /[0-9]/.test(password);
    setPasswordValid({ length, lower, upper, number });
  };

  const handlePasswordChange = (e) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    validatePassword(newPassword);
  };

  const validateName = (name) => {
    const regex = /^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$/; // Allow letters and apostrophes, up to 64 characters
    return regex.test(name);
  };

  const handleFirstNameChange = (e) => {
    const newFirstName = e.target.value;

    const formattedFirstName = newFirstName.charAt(0).toUpperCase() + newFirstName.slice(1);

    setFirstName(formattedFirstName);
    if (validateName(formattedFirstName)) {
      // setFirstName(newFirstName);
      setNameError((prev) => ({ ...prev, firstName: "" }));
    } else {
      setNameError((prev) => ({ ...prev, firstName: "The following characters are allowed: A-Z, a-z, À-Ö, Ø-ö, ø-ÿ, ', -. Maximum 64 characters." }));
    }
  };

  const handleLastNameChange = (e) => {
    const newLastName = e.target.value;

    const formattedLastName = newLastName.charAt(0).toUpperCase() + newLastName.slice(1);

    setLastName(formattedLastName);
    if (validateName(formattedLastName)) {
      // setLastName(newLastName);
      setNameError((prev) => ({ ...prev, lastName: "" }));
    } else {
      setNameError((prev) => ({ ...prev, lastName: "The following characters are allowed: A-Z, a-z, À-Ö, Ø-ö, ø-ÿ, ', -. Maximum 64 characters." }));    }
  };

  const validateEmail = async (email) => {
    // If blank, return false
    if (!email) {
      setEmailError("");
      return false;
    };

    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!regex.test(email)) {
      // Console print for debugging purposes
      setEmailError("Invalid email format");
      return false;
    }

    // TODO: Check for disposable email domains using an API
    // const isDisposable = await checkDisposableEmail(email);
    // if (isDisposable) {
    //   setEmailError("Disposable email addresses are not allowed");
    //   return false;
    // }

    // Check for role-based emails
    const roleBasedEmails = ["admin", "support", "noreply"];
    const emailLocalPart = email.split("@")[0];
    if (roleBasedEmails.includes(emailLocalPart)) {
      setEmailError("Invalid email format");
      return false;
    }

    // Check for email uniqueness (this would typically be an API call)
    const isEmailUnique = await checkEmailUniqueness(email);
    if (!isEmailUnique) {
      setEmailError("Email is already registered.");
      return false;
    }

    setEmailError("");
    return true;
  };

  const checkDisposableEmail = async (email) => {
    const response = await fetch(`https://disposable-email-api.com/api/v1/check/${email}`);
    const data = await response.json();
    return data.isDisposable;
  };

  const checkEmailUniqueness = async (email) => {
    // TODO: Add API call to check email uniqueness after implementing with AWS.
    return true; // Placeholder for actual API call
  };

  const handleEmailChange = async (e) => {
    const newEmail = e.target.value;
    setEmail(newEmail);
    await validateEmail(newEmail);
  };

  return (
    <div className="h-screen bg-gradient-to-r from-gray-700 to-gray-300 flex items-center justify-center">
      <div className="flex flex-col items-center">
        <img src="/assets/MartyChat_Full-833x200.png" alt="MartyChat Logo" className="mb-6 w-1/2" />
        <div id="signup-form" className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
          <h1 className="text-2xl font-bold mb-6 text-center text-gray-300">Create a new account.</h1>
          <form onSubmit={handleSignup}>
            <div className="flex space-x-4 mb-4">
              <div className="w-1/2">
                <label htmlFor="firstName" className="block text-sm font-medium signup-label">First Name*</label>
                <input
                  type="text"
                  id="firstName"
                  value={firstName}
                  onChange={handleFirstNameChange}
                  required
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                {nameError.firstName && <p className="mt-1 text-sm text-red-600">{nameError.firstName}</p>}
              </div>
              <div className="w-1/2">
                <label htmlFor="lastName" className="block text-sm font-medium signup-label">Last Name*</label>
                <input
                  type="text"
                  id="lastName"
                  value={lastName}
                  onChange={handleLastNameChange}
                  required
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                {nameError.lastName && <p className="mt-1 text-sm text-red-600">{nameError.lastName}</p>}
              </div>
            </div>
            <div className="mb-4">
              <label htmlFor="email" className="block text-sm font-medium signup-label">Email*</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={handleEmailChange}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
              {emailError && <p className="mt-1 text-sm text-red-600">{emailError}</p>}
            </div>
            <div className="mb-6">
              <label htmlFor="password" className="block text-sm font-medium signup-label">Password*</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={handlePasswordChange}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
              <p className="mt-2 text-sm text-gray-600">Your password must contain:</p>
              <ul className="mt-2 text-sm text-gray-600 pl-2">
                <li className={passwordValid.length ? "text-green-600" : "text-red-600"}>
                  {passwordValid.length ? "✔" : "✘"} Minimum 8 characters, Maximum 64 characters
                </li>
                <li className={passwordValid.lower ? "text-green-600" : "text-red-600"}>
                  {passwordValid.lower ? "✔" : "✘"} At least one lowercase letter
                </li>
                <li className={passwordValid.upper ? "text-green-600" : "text-red-600"}>
                  {passwordValid.upper ? "✔" : "✘"} At least one uppercase letter
                </li>
                <li className={passwordValid.number ? "text-green-600" : "text-red-600"}>
                  {passwordValid.number ? "✔" : "✘"} At least one number
                </li>
              </ul>
            </div>
            <button type="submit" id="submit-button" className="w-full py-2 px-4 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2">
              Sign Up
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
