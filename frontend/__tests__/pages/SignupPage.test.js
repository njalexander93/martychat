/**
 * @fileoverview Unit tests for the Signup Page component in MartyChat.
 * These tests validate rendering, form handling, input validation, and registration flow.
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
import SignupPage from '@/app/signup/page';

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

/**
 * Unit tests for the Signup Page component.
 */
describe('Signup Page Component', () => {
  // Setup user event for simulating user interactions
  const user = userEvent.setup();

  // Mock console methods
  console.error = jest.fn();
  console.log = jest.fn();

  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();

    // Default fetch mock to return successful signup
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: 'User created successfully!', user: 'test-user-id' }),
    });
  });

  /**
   * Test that the component renders without errors.
   */
  test('renders signup form correctly', () => {
    render(<SignupPage />);

    // Check for form elements
    expect(screen.getByRole('heading', { name: 'Create a new account.' })).toBeInTheDocument();
    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Organization/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
    expect(screen.getByText('Already have an account?')).toBeInTheDocument();
  });

  /**
   * Test that the form handles text input changes.
   */
  test('handles input field changes', async () => {
    render(<SignupPage />);

    // Get the form inputs
    const firstNameInput = screen.getByLabelText(/First Name/i);
    const lastNameInput = screen.getByLabelText(/Last Name/i);
    const organizationInput = screen.getByLabelText(/Organization/i);
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Password/i);

    // Type into the inputs
    await user.type(firstNameInput, 'John');
    await user.type(lastNameInput, 'Doe');
    await user.type(organizationInput, 'Test Organization');
    await user.type(emailInput, 'john.doe@example.com');
    await user.type(passwordInput, 'Password123');

    // Verify the input values
    expect(firstNameInput.value).toBe('John');
    expect(lastNameInput.value).toBe('Doe');
    expect(organizationInput.value).toBe('Test Organization');
    expect(emailInput.value).toBe('john.doe@example.com');
    expect(passwordInput.value).toBe('Password123');
  });

  /**
   * Test that the form performs name formatting (first letter capitalization).
   */
  test('capitalizes first letter of first and last names', async () => {
    render(<SignupPage />);

    // Type lowercase names
    await user.type(screen.getByLabelText(/First Name/i), 'john');
    await user.type(screen.getByLabelText(/Last Name/i), 'doe');

    // Verify capitalization
    expect(screen.getByLabelText(/First Name/i).value).toBe('John');
    expect(screen.getByLabelText(/Last Name/i).value).toBe('Doe');
  });

  /**
   * Test that the form validates names.
   */
  test('validates name inputs', async () => {
    render(<SignupPage />);

    // Type invalid name with numbers
    await user.type(screen.getByLabelText(/First Name/i), 'John123');

    // Check for error message
    expect(screen.getByText(/The following characters are allowed/i)).toBeInTheDocument();

    // Clear and type valid name
    await user.clear(screen.getByLabelText(/First Name/i));
    await user.type(screen.getByLabelText(/First Name/i), 'John');

    // Error should be gone
    expect(screen.queryByText(/The following characters are allowed/i)).not.toBeInTheDocument();
  });

  /**
   * Test that the form validates password complexity.
   */
  test('validates password complexity requirements', async () => {
    render(<SignupPage />);

    // Initial state - all requirements should show as not met
    expect(screen.getByText(/Minimum 8 characters/i)).toHaveClass('text-red-600');
    expect(screen.getByText(/At least one lowercase letter/i)).toHaveClass('text-red-600');
    expect(screen.getByText(/At least one uppercase letter/i)).toHaveClass('text-red-600');
    expect(screen.getByText(/At least one number/i)).toHaveClass('text-red-600');

    // Type a valid password
    await user.type(screen.getByLabelText(/Password/i), 'Password123');

    // All requirements should now be met
    expect(screen.getByText(/Minimum 8 characters/i)).toHaveClass('text-green-600');
    expect(screen.getByText(/At least one lowercase letter/i)).toHaveClass('text-green-600');
    expect(screen.getByText(/At least one uppercase letter/i)).toHaveClass('text-green-600');
    expect(screen.getByText(/At least one number/i)).toHaveClass('text-green-600');
  });

  /**
   * Test that the form validates email format.
   */
  test('validates email format', async () => {
    render(<SignupPage />);

    // Type invalid email
    await user.type(screen.getByLabelText(/Email/i), 'invalid-email');

    // Move focus to trigger validation
    await user.tab();

    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText('Invalid email format')).toBeInTheDocument();
    });

    // Clear and type valid email
    await user.clear(screen.getByLabelText(/Email/i));
    await user.type(screen.getByLabelText(/Email/i), 'valid@example.com');

    // Move focus to trigger validation
    await user.tab();

    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.queryByText('Invalid email format')).not.toBeInTheDocument();
    });
  });

  /**
   * Test that the form sanitizes user inputs.
   */
  test('sanitizes user inputs before submission', async () => {
    const sanitizeHtml = require('sanitize-html');
    render(<SignupPage />);

    // Fill out the form
    await user.type(screen.getByLabelText(/First Name/i), 'John');
    await user.type(screen.getByLabelText(/Last Name/i), 'Doe');
    await user.type(screen.getByLabelText(/Organization/i), 'Test Organization');
    await user.type(screen.getByLabelText(/Email/i), 'john.doe@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'Password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    // Check that sanitizeHtml was called for each text input
    expect(sanitizeHtml).toHaveBeenCalledWith('John');
    expect(sanitizeHtml).toHaveBeenCalledWith('Doe');
    expect(sanitizeHtml).toHaveBeenCalledWith('Test Organization');
    expect(sanitizeHtml).toHaveBeenCalledWith('john.doe@example.com');
    // Password is not sanitized
  });

  /**
   * Test that the form shows loading state during submission.
   */
  test('shows loading state during form submission', async () => {
    // Mock fetch to delay response
    global.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: () => Promise.resolve({ message: 'User created successfully!' }),
            });
          }, 100);
        })
    );

    render(<SignupPage />);

    // Fill out the form with valid data
    await user.type(screen.getByLabelText(/First Name/i), 'John');
    await user.type(screen.getByLabelText(/Last Name/i), 'Doe');
    await user.type(screen.getByLabelText(/Email/i), 'john.doe@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'Password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    // Check for loading state
    expect(screen.getByRole('button', { name: 'Creating Account...' })).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  /**
   * Test that the form handles successful submission.
   */
  test('handles successful signup submission', async () => {
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

    render(<SignupPage />);

    // Fill out the form with valid data
    await user.type(screen.getByLabelText(/First Name/i), 'John');
    await user.type(screen.getByLabelText(/Last Name/i), 'Doe');
    await user.type(screen.getByLabelText(/Organization/i), 'Test Organization');
    await user.type(screen.getByLabelText(/Email/i), 'john.doe@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'Password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    // Wait for the promise to resolve
    await waitFor(() => {
      // Check that fetch was called correctly
      expect(fetch).toHaveBeenCalledWith('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'john.doe@example.com',
          password: 'Password123',
          firstName: 'John',
          lastName: 'Doe',
          organization: 'Test Organization',
        }),
      });

      // Verify redirect occurs to login page
      expect(push).toHaveBeenCalledWith('/login');
    });
  });

  /**
   * Test that the form handles API errors.
   */
  test('handles API errors during signup', async () => {
    // Mock fetch to return an error
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ error: 'Email already exists' }),
    });

    render(<SignupPage />);

    // Fill out the form
    await user.type(screen.getByLabelText(/First Name/i), 'John');
    await user.type(screen.getByLabelText(/Last Name/i), 'Doe');
    await user.type(screen.getByLabelText(/Email/i), 'john.doe@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'Password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });

    // Verify no redirect occurred
    const { push } = require('next/navigation').useRouter();
    expect(push).not.toHaveBeenCalled();
  });

  /**
   * Test that the form handles network errors.
   */
  test('handles network errors during signup', async () => {
    // Mock fetch to throw a network error
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<SignupPage />);

    // Fill out the form
    await user.type(screen.getByLabelText(/First Name/i), 'John');
    await user.type(screen.getByLabelText(/Last Name/i), 'Doe');
    await user.type(screen.getByLabelText(/Email/i), 'john.doe@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'Password123');

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText('Signup failed. Please try again later.')).toBeInTheDocument();
    });

    // Verify console.error was called
    expect(console.error).toHaveBeenCalledWith('Error creating user:', expect.any(Error));
  });

  /**
   * Test that the form link navigates to login page.
   */
  test('navigates to login page when "Already have an account?" link is clicked', async () => {
    render(<SignupPage />);

    const loginLink = screen.getByText('Already have an account?');

    // Verify link goes to login page
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  /**
   * Test that the form handles submission with empty required fields.
   */
  test('handles submission with empty required fields', async () => {
    // Mock fetch to return an error for empty fields
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ error: 'All required fields must be filled.' }),
    });

    render(<SignupPage />);

    // Leave required fields empty and submit the form
    // Only fill organization which is optional
    await user.type(screen.getByLabelText(/Organization/i), 'Test Organization');

    // Get the form element
    const form = screen.getByRole('button', { name: 'Sign Up' }).closest('form');

    // Directly submit the form to bypass browser's built-in form validation
    fireEvent.submit(form);

    // Verify that fetch was called with empty required fields
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: expect.stringContaining('"firstName":""'),
      });
    });

    // The backend should return an error and the component should display it
    await waitFor(() => {
      expect(screen.getByText('All required fields must be filled.')).toBeInTheDocument();
    });
  });

  /**
   * Test that the password validation updates as user types.
   */
  test('updates password validation in real-time as user types', async () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText(/Password/i);

    // Start with empty password
    expect(screen.getByText(/Minimum 8 characters/i)).toHaveClass('text-red-600');

    // Step 1: Type a short password
    await user.type(passwordInput, 'short');
    expect(screen.getByText(/Minimum 8 characters/i)).toHaveClass('text-red-600');
    expect(screen.getByText(/At least one lowercase letter/i)).toHaveClass('text-green-600');
    expect(screen.getByText(/At least one uppercase letter/i)).toHaveClass('text-red-600');
    expect(screen.getByText(/At least one number/i)).toHaveClass('text-red-600');

    // Step 2: Add more characters to make it long enough
    await user.type(passwordInput, 'enough');
    expect(screen.getByText(/Minimum 8 characters/i)).toHaveClass('text-green-600');

    // Step 3: Add uppercase
    await user.clear(passwordInput);
    await user.type(passwordInput, 'shortenoughA');
    expect(screen.getByText(/At least one uppercase letter/i)).toHaveClass('text-green-600');

    // Step 4: Add number
    await user.clear(passwordInput);
    await user.type(passwordInput, 'shortenoughA1');
    expect(screen.getByText(/At least one number/i)).toHaveClass('text-green-600');

    // All criteria should now be met
    expect(screen.getByText(/Minimum 8 characters/i)).toHaveClass('text-green-600');
    expect(screen.getByText(/At least one lowercase letter/i)).toHaveClass('text-green-600');
    expect(screen.getByText(/At least one uppercase letter/i)).toHaveClass('text-green-600');
    expect(screen.getByText(/At least one number/i)).toHaveClass('text-green-600');
  });
});
