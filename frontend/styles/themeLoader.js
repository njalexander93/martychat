/**
 * @fileoverview Theme loader for the MartyChat application
 * This file loads the theme configuration into the application.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-04
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

'use client';

import { useEffect } from 'react';
import { cssVariables } from './theme';

export function ThemeLoader() {
  useEffect(() => {
    // Only run on client side
    const style = document.createElement('style');
    style.textContent = cssVariables;
    document.head.appendChild(style);

    // Cleanup on unmount
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return null;
}

export default ThemeLoader;
