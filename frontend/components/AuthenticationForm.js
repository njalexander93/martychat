/**
 * @fileoverview Authentication form template for the MartyChat application.
 * This file defines the layout for the signup and login pages.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-04
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import Link from "next/link";

/**
 * Authentication form component.
 *
 * @param {Object} props - The component props.
 */
export default function AuthenticationForm({ children }) {
  return (
    <div className="h-screen bg-gradient-to-l from-[var(--color-bg-secondary)] from-20% to-[var(--color-bg-dark)] to-100% flex items-center justify-center">
      <div className="flex flex-col items-center">
        <Link href="/" className="mb-6 w-1/2 unselectable">
          <img src="/assets/MartyChat_Full-833x200.png" alt="MartyChat Logo"  />
        </Link>
        <div id="authentication-form"  className="p-8 rounded-lg shadow-lg w-full max-w-md auth-form-text">
            {children}
        </div>
      </div>
    </div>
  );
}
