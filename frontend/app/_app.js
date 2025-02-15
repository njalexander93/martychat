/**
 * @fileoverview Custom App component for Next.js.
 * This file is used to initialize pages. It can be used to keep state when navigating between pages.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-04
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import './globals.css';

/**
 * Custom App component for Next.js.
 *
 * @param {Object} props - The component props.
 * @param {React.Component} props.Component - The active page component.
 * @param {Object} props.pageProps - The initial props for the active page component.
 * @returns {React.Element} The rendered component.
 */
function MyApp({ Component, pageProps }) {
  return <Component {...pageProps} />;
}

export default MyApp;
