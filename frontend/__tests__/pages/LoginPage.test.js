/**
 * @fileoverview Unit tests for the Login Page component in MartyChat.
 * These tests validate rendering, form handling, input validation, and authentication flow.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from '@/app/login/page';

// Mock the next/navigation module (already handled in jest.setup.js)

// Mock sanitize-html
jest.mock('sanitize-html', () => jest.fn((input) => input));

// Mock AuthenticationForm component to simplify testing
jest.mock('@/components/AuthenticationForm', () => {
  const AuthFormMock = ({ children }) => <div data-testid="auth-form-mock">{children}</div>;
  AuthFormMock.displayName = 'AuthenticationForm';
  return AuthFormMock;
});

// Mock fetch for testing API calls
global.fetch = jest.fn();

// Mock localStorage for storing authentication tokens
const localStorageMock = (function () {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock sessionStorage for storing user ID
const sessionStorageMock = (function () {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});

/**
 * Unit tests for the Login Page component.
 */
describe('Login Page Component', () => {
  // Setup user event for simulating user interactions
  const user = userEvent.setup();

  // Mock console methods
  console.error = jest.fn();
  console.log = jest.fn();

  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    sessionStorageMock.clear();
    document.cookie = '';

    // Default fetch mock to return successful login
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          authenticationResult: {
            IdToken: 'mock-id-token',
            AccessToken: 'mock-access-token',
            RefreshToken: 'mock-refresh-token',
            IdTokenExpires: 3600,
            AccessTokenExpires: 3600,
            RefreshTokenExpires: 86400,
            UserId: 'mock-user-id',
          },
        }),
    });
  });

  /**
   * Test that the component renders without errors.
   */
  test('renders login form correctly', () => {
    render(<Login />);

    // Check for form elements
    expect(screen.getByRole('heading', { name: 'Sign In' })).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
    expect(screen.getByText('Create an account')).toBeInTheDocument();
  });

  /**
   * Test that the form handles email input changes.
   */
  test('handles email input changes', async () => {
    render(<Login />);

    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    expect(emailInput.value).toBe('test@example.com');
  });

  /**
   * Test that the form handles password input changes.
   */
  test('handles password input changes', async () => {
    render(<Login />);

    const passwordInput = screen.getByLabelText('Password');
    await user.type(passwordInput, 'password123');

    expect(passwordInput.value).toBe('password123');
  });

  /**
   * Test that the form shows an error when fields are empty.
   */
  test('shows error when fields are empty', async () => {
    render(<Login />);

    // Get the form element
    const form = screen.getByRole('button', { name: 'Sign In' }).closest('form');

    // Directly submit the form to bypass browser's built-in form validation
    // This is needed because inputs have the "required" attribute which would
    // prevent submission at the browser level
    fireEvent.submit(form);

    // Wait for the error state to be processed
    await waitFor(() => {
      // The loginError state should be set
      expect(screen.getByText('Email and password are required.')).toBeInTheDocument();
    });

    // Ensure API was not called
    expect(fetch).not.toHaveBeenCalled();
  });

  /**
   * Test that the form sanitizes email input.
   */
  test('sanitizes email input before submission', async () => {
    const sanitizeHtml = require('sanitize-html');
    render(<Login />);

    // Fill out the form
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Check that sanitizeHtml was called with the email
    expect(sanitizeHtml).toHaveBeenCalledWith('test@example.com');
  });

  /**
   * Test that the form shows loading state during submission.
   */
  test('shows loading state during form submission', async () => {
    // Mock fetch to delay resolution
    global.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: () =>
                Promise.resolve({
                  authenticationResult: {
                    IdToken: 'mock-id-token',
                    AccessToken: 'mock-access-token',
                    RefreshToken: 'mock-refresh-token',
                    IdTokenExpires: 3600,
                    AccessTokenExpires: 3600,
                    RefreshTokenExpires: 86400,
                    UserId: 'mock-user-id',
                  },
                }),
            });
          }, 100);
        })
    );

    render(<Login />);

    // Fill out the form
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Check for loading state
    expect(screen.getByRole('button', { name: 'Signing in...' })).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  /**
   * Test that the form handles successful submission.
   */
  test('handles successful login submission', async () => {
    // Clear and re-mock router
    const push = jest.fn();
    jest.spyOn(require('next/navigation'), 'useRouter').mockImplementation(() => ({
      push,
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    }));

    render(<Login />);

    // Fill out the form
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Wait for the promise to resolve
    await waitFor(() => {
      // Check that fetch was called correctly
      expect(fetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
      });

      // Verify tokens are stored in localStorage
      expect(localStorageMock.setItem).toHaveBeenCalledWith('idToken', 'mock-id-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('accessToken', 'mock-access-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refreshToken', 'mock-refresh-token');

      // Verify expiration times are stored
      expect(localStorageMock.setItem).toHaveBeenCalledWith('idTokenExpires', expect.any(Number));
      expect(localStorageMock.setItem).toHaveBeenCalledWith('accessTokenExpires', expect.any(Number));
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refreshTokenExpires', expect.any(Number));

      // Verify user ID is stored in sessionStorage
      expect(sessionStorageMock.setItem).toHaveBeenCalledWith('userId', 'mock-user-id');

      // Verify cookie is set
      expect(document.cookie).toContain('idToken=mock-id-token');

      // Verify redirect occurs
      expect(push).toHaveBeenCalledWith('/marty');
    });
  });

  /**
   * Test that the form handles API errors.
   */
  test('handles API errors during login', async () => {
    // Mock fetch to return an error
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ error: 'Invalid credentials' }),
    });

    render(<Login />);

    // Fill out the form
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText('Sign in failed. Please try again later.')).toBeInTheDocument();
    });

    // Verify no redirect occurred
    const { push } = require('next/navigation').useRouter();
    expect(push).not.toHaveBeenCalled();
  });

  /**
   * Test that the form handles network errors.
   */
  test('handles network errors during login', async () => {
    // Mock fetch to throw a network error
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<Login />);

    // Fill out the form
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText('Sign in failed. Please try again later.')).toBeInTheDocument();
    });

    // Verify console.error was called
    expect(console.error).toHaveBeenCalledWith('Error logging in:', expect.any(Error));
  });

  /**
   * Test that the form respects callback URLs.
   */
  test('respects callback URL for redirect after login', async () => {
    const { push } = require('next/navigation').useRouter();

    // Mock window.location.search
    const originalLocation = window.location;
    delete window.location;
    window.location = {
      ...originalLocation,
      search: '?callbackUrl=/dashboard',
    };

    render(<Login />);

    // Fill out the form
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Wait for the promise to resolve
    await waitFor(() => {
      // Verify redirect to callback URL
      expect(push).toHaveBeenCalledWith('/dashboard');
    });

    // Restore original location
    window.location = originalLocation;
  });

  /**
   * Test that the form link navigates to signup page.
   */
  test('navigates to signup page when create account link is clicked', async () => {
    render(<Login />);

    const createAccountLink = screen.getByText('Create an account');

    // Verify link goes to signup page
    expect(createAccountLink).toHaveAttribute('href', '/signup');
  });
});
