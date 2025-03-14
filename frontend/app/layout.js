/**
 * @fileoverview Layout component for the MartyChat application.
 * This file defines the layout for the application, including global styles and metadata.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-04
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import { Roboto, Roboto_Slab, Roboto_Flex, Roboto_Mono, Roboto_Serif } from 'next/font/google';
import './globals.css';
import { ThemeLoader } from '@/styles/themeLoader';
import { Metadata } from 'next';

/**
 * Metadata for the application.
 * @type {Object}
 */
export const metadata = {
  title: 'MartyChat • Your AI-Powered Psychology Assistant',
  description: 'Your AI-Powered Psychology Assistant.',
};

/**
 * Load Google Fonts: Roboto Flex and Roboto Slab.
 */
const roboto = Roboto({ variable: '--font-roboto', weight: '300', subsets: ['latin'], display: 'swap' });
const robotoSlab = Roboto_Slab({ variable: '--font-roboto-slab', subsets: ['latin'], display: 'swap' });
const robotoFlex = Roboto_Flex({ variable: '--font-roboto-flex', subsets: ['latin'], display: 'swap' });
const robotoMono = Roboto_Mono({ variable: '--font-roboto-mono', subsets: ['latin'], display: 'swap' });
const robotoSerif = Roboto_Serif({ variable: '--font-roboto-serif', subsets: ['latin'], display: 'swap' });

// Combine all font variables for body class
const fontVariables = `${roboto.variable} ${robotoSlab.variable} ${robotoFlex.variable} ${robotoMono.variable} ${robotoSerif.variable}`;

/**
 * Root layout component for the MartyChat application.
 *
 * @param {Object} props - The component props.
 * @param {React.ReactNode} props.children - The child components to be rendered within the layout.
 * @returns {React.Element} The rendered layout component.
 */
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${fontVariables} antialiased bg-bg-primary text-text-primary`}>
        <ThemeLoader />
        {children}
      </body>
    </html>
  );
}
