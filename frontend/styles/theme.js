/**
 * @fileoverview Theme configuration for the MartyChat application.
 * This file defines the theme configuration for the application.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-28
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

// CSS Custom Properties and Theme Configuration
export const themeConfig = {
  colors: {
    primary: {
      DEFAULT: '#630917',
      hover: '#771424',
      active: '#510D18',
    },
    secondary: {
      DEFAULT: '#4D4D4C',
      hover: '#5F5F5E',
      active: '#3D3D3C',
    },
    accent: {
      DEFAULT: '#8B4D4D',
      hover: '#A25959',
      active: '#743F3F',
    },
    text: {
      primary: '#2D2D2D',
      secondary: '#424241',
      input: '#717171',
      light: '#F8F6F6',
    },
    background: {
      input: '#F3F4F6',
      primary: '#E5E7EB',
      secondary: '#D1D5DB',
      dark: '#374151',
    },
  },
  fonts: {
    roboto: 'Roboto',
    robotoSlab: 'Roboto Slab',
    robotoFlex: 'Roboto Flex',
  },
};

// Generate CSS Variables
export const cssVariables = `
  :root {
    /* Primary Colors */
    --color-primary: ${themeConfig.colors.primary.DEFAULT};
    --color-primary-hover: ${themeConfig.colors.primary.hover};
    --color-primary-active: ${themeConfig.colors.primary.active};

    /* Secondary Colors */
    --color-secondary: ${themeConfig.colors.secondary.DEFAULT};
    --color-secondary-hover: ${themeConfig.colors.secondary.hover};
    --color-secondary-active: ${themeConfig.colors.secondary.active};

    /* Accent Colors */
    --color-accent: ${themeConfig.colors.accent.DEFAULT};
    --color-accent-hover: ${themeConfig.colors.accent.hover};
    --color-accent-active: ${themeConfig.colors.accent.active};

    /* Text Colors */
    --color-text-primary: ${themeConfig.colors.text.primary};
    --color-text-secondary: ${themeConfig.colors.text.secondary};
    --color-text-input: ${themeConfig.colors.text.input};
    --color-text-light: ${themeConfig.colors.text.light};

    /* Background Colors */
    --color-bg-input: ${themeConfig.colors.background.input};
    --color-bg-primary: ${themeConfig.colors.background.primary};
    --color-bg-secondary: ${themeConfig.colors.background.secondary};
    --color-bg-dark: ${themeConfig.colors.background.dark};

    /* Fonts */
    --font-roboto: ${themeConfig.fonts.roboto};
    --font-roboto-slab: ${themeConfig.fonts.robotoSlab};
    --font-roboto-flex: ${themeConfig.fonts.robotoFlex};
  }
`;

// Tailwind Colors Configuration
export const tailwindColors = {
  primary: {
    DEFAULT: 'var(--color-primary)',
    hover: 'var(--color-primary-hover)',
    active: 'var(--color-primary-active)',
  },
  secondary: {
    DEFAULT: 'var(--color-secondary)',
    hover: 'var(--color-secondary-hover)',
    active: 'var(--color-secondary-active)',
  },
  accent: {
    DEFAULT: 'var(--color-accent)',
    hover: 'var(--color-accent-hover)',
    active: 'var(--color-accent-active)',
  },
  text: {
    primary: 'var(--color-text-primary)',
    secondary: 'var(--color-text-secondary)',
    input: 'var(--color-text-input)',
    light: 'var(--color-text-light)',
  },
  bg: {
    primary: 'var(--color-bg-primary)',
    secondary: 'var(--color-bg-secondary)',
    dark: 'var(--color-bg-dark)',
    input: 'var(--color-bg-input)',
  },
};
