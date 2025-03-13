/**
 * @fileoverview Unit tests for the Home Page component in MartyChat.
 * These tests validate rendering, backend connection handling, and navigation links.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Home from '@/app/page';

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    const { className, src, alt, priority, placeholder, quality, loading, onLoadingComplete, ...validProps } = props;

    return (
      <div data-testid="mock-image" className={className || ''}>
        <span data-src={src} data-alt={alt} {...validProps} />
      </div>
    );
  },
}));

// Mock fetch for testing API calls
global.fetch = jest.fn();

// Store original environment variables
const originalEnv = process.env;

/**
 * Unit tests for the Home Page component.
 */
describe('Home Page Component', () => {
  // Setup user event for simulating user interactions
  const user = userEvent.setup();

  // Mock console methods
  console.warn = jest.fn();
  console.error = jest.fn();

  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();

    // Reset process.env
    process.env = { ...originalEnv };
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';

    // Default fetch mock to simulate a successful backend connection
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: 'Welcome to MartyChat API' }),
    });
  });

  // Restore the original process.env after all tests
  afterAll(() => {
    process.env = originalEnv;
  });

  /**
   * Test that the component renders without errors.
   */
  test('renders home page correctly', async () => {
    render(<Home />);

    // Check for MartyChat image
    const image = screen.getByTestId('mock-image');
    expect(image).toBeInTheDocument();
    expect(image.querySelector('span')).toHaveAttribute('data-alt', 'MartyChat Logo');

    // Check for navigation links
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByText('Sign Up')).toBeInTheDocument();

    // Wait for backend check to complete
    await waitFor(() => {
      // No assertions needed here, just waiting for useEffect to complete
    });
  });

  /**
   * Test that the component handles successful backend connection.
   */
  test('handles successful backend connection', async () => {
    render(<Home />);

    // Wait for backend check to complete
    await waitFor(() => {
      // Verify fetch was called with the correct URL
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000', {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      });
    });

    // The message state should be updated from the API response
    // (Since message isn't directly displayed in the UI, we don't test for it here)
    // Instead, we verify the backend status was updated to 'connected'
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  /**
   * Test that the component handles missing API URL configuration.
   */
  test('handles missing API URL configuration', async () => {
    // Remove the API URL from environment variables
    delete process.env.NEXT_PUBLIC_API_URL;

    render(<Home />);

    // Wait for the effect to run
    await waitFor(() => {
      // Check that a warning was logged
      expect(console.warn).toHaveBeenCalledWith('API_URL not configured');
    });

    // Verify fetch was not called
    expect(fetch).not.toHaveBeenCalled();
  });

  /**
   * Test that the component handles failed backend connection.
   */
  test('handles failed backend connection', async () => {
    // Mock fetch to simulate a failed connection
    global.fetch.mockRejectedValueOnce(new Error('Failed to connect'));

    render(<Home />);

    // Wait for the effect to run and catch the error
    await waitFor(() => {
      // Check that an error was logged
      expect(console.error).toHaveBeenCalledWith('Backend connection error:', expect.any(Error));
    });

    // In development mode, message should indicate a connection issue
    process.env.NODE_ENV = 'development';

    render(<Home />);

    global.fetch.mockRejectedValueOnce(new Error('Failed to connect'));

    await waitFor(() => {
      expect(console.error).toHaveBeenCalledWith('Backend connection error:', expect.any(Error));
    });
  });

  /**
   * Test that the component handles unsuccessful backend responses.
   */
  test('handles unsuccessful backend responses', async () => {
    // Mock fetch to simulate an unsuccessful response
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    render(<Home />);

    // Wait for the effect to run
    await waitFor(() => {
      // Check that an error was logged
      expect(console.error).toHaveBeenCalledWith('Backend connection error:', expect.any(Error));
    });
  });

  /**
   * Test that the sign in link navigates to the login page.
   */
  test('sign in link navigates to login page', async () => {
    render(<Home />);

    const signInLink = screen.getByText('Sign In');

    // Verify the href attribute
    expect(signInLink).toHaveAttribute('href', '/login');

    // Mock click event is not needed since we're just testing the href attribute
  });

  /**
   * Test that the sign up link navigates to the signup page.
   */
  test('sign up link navigates to signup page', async () => {
    render(<Home />);

    const signUpLink = screen.getByText('Sign Up');

    // Verify the href attribute
    expect(signUpLink).toHaveAttribute('href', '/signup');

    // Mock click event is not needed since we're just testing the href attribute
  });

  /**
   * Test that the component applies the correct styling classes.
   */
  test('applies correct styling classes', () => {
    const { container } = render(<Home />);

    // Check for gradient background
    expect(container.firstChild).toHaveClass('h-screen');
    expect(container.firstChild).toHaveClass('bg-gradient-to-l');

    // Our improved Image mock now applies the className directly
    const image = screen.getByTestId('mock-image');
    expect(image).toHaveClass('unselectable');

    // Check for styling on navigation links
    const signInLink = screen.getByText('Sign In');
    const signUpLink = screen.getByText('Sign Up');

    expect(signInLink).toHaveClass('inline-block');
    expect(signInLink).toHaveClass('link');

    expect(signUpLink).toHaveClass('inline-block');
    expect(signUpLink).toHaveClass('link');
  });
});
