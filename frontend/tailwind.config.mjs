/**
 * @fileoverview Tailwind configuration for the MartyChat application.
 * This file defines the Tailwind CSS configuration.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import { tailwindColors } from './styles/theme.js';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ...tailwindColors,
      },
      backgroundColor: {
        ...Object.entries(tailwindColors.bg).reduce((acc, [key, value]) => {
          acc[`bg-${key}`] = value;
          return acc;
        }, {})
      },
      fontFamily: {
        'roboto': ['var(--font-roboto)'],
        'roboto-slab': ['var(--font-roboto-slab)'],
        'roboto-flex': ['var(--font-roboto-flex)'],
      },
    },
  },
  plugins: [],
};
