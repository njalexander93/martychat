/**
 * @fileoverview Unit tests for the RootLayout component in MartyChat.
 * These tests validate the global layout structure, font loading, and theme application.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import React from 'react';
import { render } from '@testing-library/react';
import RootLayout from '@/app/layout';

// Mock the next/font modules
jest.mock('next/font/google', () => ({
  Roboto: jest.fn().mockReturnValue({
    variable: '--font-roboto',
    weight: '300',
    subsets: ['latin'],
    display: 'swap',
  }),
  Roboto_Slab: jest.fn().mockReturnValue({
    variable: '--font-roboto-slab',
    subsets: ['latin'],
    display: 'swap',
  }),
  Roboto_Flex: jest.fn().mockReturnValue({
    variable: '--font-roboto-flex',
    subsets: ['latin'],
    display: 'swap',
  }),
  Roboto_Mono: jest.fn().mockReturnValue({
    variable: '--font-roboto-mono',
    subsets: ['latin'],
    display: 'swap',
  }),
  Roboto_Serif: jest.fn().mockReturnValue({
    variable: '--font-roboto-serif',
    subsets: ['latin'],
    display: 'swap',
  }),
}));

// Mock the ThemeLoader component
jest.mock('@/styles/themeLoader', () => ({
  ThemeLoader: jest.fn(() => <div data-testid="theme-loader-mock" />),
}));

/**
 * Unit tests for the RootLayout component.
 */
describe('RootLayout Component', () => {
  /**
   * Test that the component renders without errors.
   */
  test('renders without crashing', () => {
    render(
      <RootLayout>
        <div data-testid="test-child">Test Content</div>
      </RootLayout>
    );

    // Check if root tags are rendered properly
    const htmlElement = document.querySelector('html');
    const bodyElement = document.querySelector('body');
    const testChild = document.querySelector('[data-testid="test-child"]');

    expect(htmlElement).toBeInTheDocument();
    expect(bodyElement).toBeInTheDocument();
    expect(testChild).toBeInTheDocument();
    expect(testChild.textContent).toBe('Test Content');
  });

  /**
   * Test that the component sets language attribute on html tag.
   */
  test('sets the correct language attribute on html tag', () => {
    render(
      <RootLayout>
        <div>Test Content</div>
      </RootLayout>
    );

    const htmlElement = document.querySelector('html');
    expect(htmlElement).toHaveAttribute('lang', 'en');
  });

  /**
   * Test that the component applies font variables to body.
   */
  test('applies all font variables to body', () => {
    render(
      <RootLayout>
        <div>Test Content</div>
      </RootLayout>
    );

    const bodyElement = document.querySelector('body');

    expect(bodyElement.className).toContain('--font-roboto');
    expect(bodyElement.className).toContain('--font-roboto-slab');
    expect(bodyElement.className).toContain('--font-roboto-flex');
    expect(bodyElement.className).toContain('--font-roboto-mono');
    expect(bodyElement.className).toContain('--font-roboto-serif');
  });

  /**
   * Test that the component applies proper CSS classes to body.
   */
  test('applies appropriate CSS classes to body', () => {
    render(
      <RootLayout>
        <div>Test Content</div>
      </RootLayout>
    );

    const bodyElement = document.querySelector('body');

    expect(bodyElement).toHaveClass('antialiased');
    expect(bodyElement).toHaveClass('bg-bg-primary');
    expect(bodyElement).toHaveClass('text-text-primary');
  });

  /**
   * Test that the component renders ThemeLoader component.
   */
  test('renders the ThemeLoader component', () => {
    const { getByTestId } = render(
      <RootLayout>
        <div>Test Content</div>
      </RootLayout>
    );

    expect(getByTestId('theme-loader-mock')).toBeInTheDocument();
  });

  /**
   * Test that the component renders children correctly.
   */
  test('renders children correctly', () => {
    const { getByText } = render(
      <RootLayout>
        <div>Child Component 1</div>
        <div>Child Component 2</div>
      </RootLayout>
    );

    expect(getByText('Child Component 1')).toBeInTheDocument();
    expect(getByText('Child Component 2')).toBeInTheDocument();
  });

  /**
   * Test that the component correctly combines font variables in body class.
   */
  test('combines all font variables in body class', () => {
    render(
      <RootLayout>
        <div>Test Content</div>
      </RootLayout>
    );

    // Access body element directly from document
    const bodyElement = document.body;
    expect(bodyElement).not.toBeNull();

    const bodyClassNames = bodyElement.className;
    const expectedFontVariables = [
      '--font-roboto',
      '--font-roboto-slab',
      '--font-roboto-flex',
      '--font-roboto-mono',
      '--font-roboto-serif',
    ].join(' ');

    expect(bodyClassNames).toContain(expectedFontVariables);
  });
});
