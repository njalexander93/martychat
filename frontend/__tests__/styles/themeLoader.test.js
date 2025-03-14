/**
 * @fileoverview Unit tests for the ThemeLoader component in MartyChat.
 * These tests validate rendering, CSS variables injection, and cleanup on unmount.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import React from 'react';
import { render, cleanup } from '@testing-library/react';
import { ThemeLoader } from '@/styles/themeLoader';
import { cssVariables } from '@/styles/theme';

/**
 * Unit tests for the ThemeLoader component.
 */
describe('ThemeLoader Component', () => {
  // Track created style elements for cleanup
  let styleElements = [];

  // Store original createElement to restore later
  const originalCreateElement = document.createElement;

  // Mock createElement to track style elements
  beforeEach(() => {
    styleElements = [];

    // Mock document.createElement to track created style elements
    document.createElement = function (tagName) {
      const element = originalCreateElement.call(document, tagName);
      if (tagName.toLowerCase() === 'style') {
        styleElements.push(element);
      }
      return element;
    };

    // Mock document.head.appendChild to prevent actual DOM changes
    jest.spyOn(document.head, 'appendChild').mockImplementation((element) => {
      return element;
    });

    // Mock document.head.removeChild to prevent errors during cleanup
    jest.spyOn(document.head, 'removeChild').mockImplementation((element) => {
      return element;
    });
  });

  // Clean up after each test
  afterEach(() => {
    document.createElement = originalCreateElement;
    document.head.appendChild.mockRestore();
    document.head.removeChild.mockRestore();
    styleElements = [];
    cleanup();
  });

  /**
   * Test that the component renders without errors.
   */
  test('renders without crashing', () => {
    const { unmount } = render(<ThemeLoader />);
    unmount();
    // Test passes if render doesn't throw
  });

  /**
   * Test that the component returns null (no visible output).
   */
  test('returns null (no visible output)', () => {
    const { container, unmount } = render(<ThemeLoader />);
    // The component should not add anything to the DOM container
    expect(container.firstChild).toBeNull();
    unmount();
  });

  /**
   * Test that the component injects CSS variables into document head.
   */
  test('injects CSS variables into document head', () => {
    const { unmount } = render(<ThemeLoader />);

    // Verify appendChild was called on document.head
    expect(document.head.appendChild).toHaveBeenCalled();

    // Verify at least one style element was created
    expect(styleElements.length).toBeGreaterThan(0);

    // Verify the last created style element contains the CSS variables
    const styleElement = styleElements[styleElements.length - 1];
    expect(styleElement.textContent).toBe(cssVariables);

    unmount();
  });

  /**
   * Test that the component cleans up on unmount.
   */
  test('cleans up on unmount', () => {
    const { unmount } = render(<ThemeLoader />);

    // Verify style was added
    expect(document.head.appendChild).toHaveBeenCalled();

    // Unmount the component
    unmount();

    // Verify removeChild was called
    expect(document.head.removeChild).toHaveBeenCalled();
  });

  /**
   * Test that the component only creates one style element.
   */
  test('creates only one style element', () => {
    render(<ThemeLoader />);

    // There should be only one style element created
    expect(styleElements.length).toBe(1);

    // Clean up manually to avoid test interference
    cleanup();
  });

  /**
   * Test that the component creates a proper style element.
   */
  test('creates a proper style element', () => {
    render(<ThemeLoader />);

    // Get the created style element
    expect(styleElements.length).toBeGreaterThan(0);
    const styleElement = styleElements[0];

    // Verify it's a style element
    expect(styleElement.tagName.toLowerCase()).toBe('style');

    // Verify the content
    expect(styleElement.textContent).toContain('--color-primary:');
    expect(styleElement.textContent).toContain('--color-text-primary:');
    expect(styleElement.textContent).toContain('--font-roboto:');

    cleanup();
  });

  /**
   * Test that the component uses the same CSS variables from theme.js.
   */
  test('uses CSS variables from theme.js', () => {
    render(<ThemeLoader />);

    // Get the created style element
    expect(styleElements.length).toBeGreaterThan(0);
    const styleElement = styleElements[0];

    // Verify that the content matches cssVariables from theme.js
    expect(styleElement.textContent).toBe(cssVariables);

    // Verify specific variables from the theme are present
    const themeVars = [
      '--color-primary:',
      '--color-secondary:',
      '--color-accent:',
      '--color-text-primary:',
      '--color-bg-primary:',
      '--font-roboto:',
      '--font-roboto-slab:',
      '--font-roboto-flex:',
    ];

    themeVars.forEach((variable) => {
      expect(styleElement.textContent).toContain(variable);
    });

    cleanup();
  });
});
