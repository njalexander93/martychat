/**
 * @fileoverview Signup page component for the MartyChat application.
 * This file defines the signup page, including form handling and validation.
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
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthenticationForm from "@/components/AuthenticationForm";
import sanitizeHtml from "sanitize-html";

/**
 * Signup page component.
 *
 * @returns {React.Element} The rendered signup page component.
 */
export default function SignupPage() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [organization, setOrganization] = useState("");
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
  const [signupError, setSignupError] = useState(""); // Initialize signupError state
  const [isLoading, setIsLoading] = useState(false);

  const router = useRouter();

  /**
   * Handles the signup form submission.
   *
   * @param {React.FormEvent<HTMLFormElement>} e - The form submission event.
   */
  const handleSignup = async (e) => {
    e.preventDefault();
    setSignupError("");
    setIsLoading(true);

    // Sanitize the user input
    const sanitizedFirstName = sanitizeHtml(firstName);
    const sanitizedLastName = sanitizeHtml(lastName);
    const sanitizedEmail = sanitizeHtml(email);
    const sanitizedOrganization = sanitizeHtml(organization);

    // Add user input to a json format
    const signupData = {
      email: sanitizedEmail,
      password: password,
      firstName: sanitizedFirstName,
      lastName: sanitizedLastName,
      organization: sanitizedOrganization
    };

    try {
      // Create a new user in Cognito and DynamoDB with the create-user Lambda function.
      const response = await fetch("/api/auth/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(signupData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error creating user:", errorData);
        setSignupError(errorData.error || "Unknown error");
        return;
      }

      const responseData = await response.json();
      console.log("User created successfully:", responseData);
      // alert("User created successfully. Please check your email for a verification link.");
      setSignupError("");
      router.push("/login"); // Redirect to the login page
    }
    catch (error) {
      console.error("Error creating user:", error);
      setSignupError("Signup failed. Please try again later.");
    }
    finally {
      setIsLoading(false);
    }
  };

  /**
   * Validates the password based on length, lowercase, uppercase, and number criteria.
   *
   * @param {string} password - The password to validate.
   */
  const validatePassword = (password) => {
    const length = password.length >= 8 && password.length <= 64;
    const lower = /[a-z]/.test(password);
    const upper = /[A-Z]/.test(password);
    const number = /[0-9]/.test(password);
    setPasswordValid({ length, lower, upper, number });
  };

  /**
   * Handles password input change and validates the password.
   *
   * @param {React.ChangeEvent<HTMLInputElement>} e - The input change event.
   */
  const handlePasswordChange = (e) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    validatePassword(newPassword);
  };

  /**
   * Validates the name based on the regex pattern. The name can contain letters, apostrophes, and hyphens. The name can
   * be up to 64 characters long.
   *
   * @param {string} name - The name to validate.
   */
  const validateName = (name) => {
    const regex = /^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$/; // Allow letters and apostrophes, up to 64 characters
    return regex.test(name);
  };

  /**
   * Handles first name input change and validates the first name.
   *
   * @param {React.ChangeEvent<HTMLInputElement>} e - The input change event.
   */
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

  /**
   * Handles last name input change and validates the last name.
   *
   * @param {React.ChangeEvent<HTMLInputElement>} e - The input change event.
   */
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

  /**
   * Handles organization input change.
   *
   * @param {React.ChangeEvent<HTMLInputElement>} e - The input change event.
    */
  const handleOrganizationChange = (e) => {
    const newOrganization = e.target.value;
    setOrganization(newOrganization);
  };

  /**
   * Validates the email based on the regex pattern, checks for role-based emails, and checks for email uniqueness.
   *
   * @param {string} email - The email to validate.
   */
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

  /**
   * Checks if the email is a disposable email address using the Disposable Email API.
   *
   * @param {string} email - The email to check.
   */
  const checkDisposableEmail = async (email) => {
    // TODO: Fix this. The API is not working.
    const response = await fetch(`https://disposable-email-api.com/api/v1/check/${email}`);
    const data = await response.json();
    return data.isDisposable;
  };

  /**
   * Checks if the email is unique in the database.
   *
   * @param {string} email - The email to check.
   */
  const checkEmailUniqueness = async (email) => {
    // TODO: Add API call to check email uniqueness after implementing with AWS.
    return true; // Placeholder for actual API call
  };

  /**
   * Handles email input change and validates the email.
   *
   * @param {React.ChangeEvent<HTMLInputElement>} e - The input change event.
   */
  const handleEmailChange = async (e) => {
    const newEmail = e.target.value;
    setEmail(newEmail);
    await validateEmail(newEmail);
  };

  return (
    <AuthenticationForm>
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
              disabled={isLoading}
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
              disabled={isLoading}
            />
            {nameError.lastName && <p className="mt-1 text-sm text-red-600">{nameError.lastName}</p>}
          </div>
        </div>
        <div className="mb-4">
          <label htmlFor="organization" className="block text-sm font-medium signup-label">Organization</label>
          <input
            type="text"
            id="organization"
            value={organization}
            onChange={handleOrganizationChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            disabled={isLoading}
          />
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
            disabled={isLoading}
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
            disabled={isLoading}
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
        <button
          type="submit"
          className={`w-full py-2 px-4 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 submit-button ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          disabled={isLoading}
        >
          {isLoading ? 'Creating Account...' : 'Sign Up'}
        </button>
        <div className="mt-4 text-center">
          {signupError && <p className="mt-2 text-sm text-red-600">{signupError}</p>} {/* Display the signup error message */}
        </div>
        <div className="mt-4 text-center">
          <Link href="/login" className="text-sm">
            Already have an account?
          </Link>
        </div>
      </form>
    </AuthenticationForm>
  );
}
