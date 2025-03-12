/**
 * @fileoverview Unit tests for the AuthenticationForm component in MartyChat.
 * These tests validate rendering, props handling, and child component inclusion.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import AuthenticationForm from '@/components/AuthenticationForm';

// Mock the Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    // Extract priority and other Next.js specific props to avoid React warnings

    const { priority, placeholder, quality, loading, onLoadingComplete, ...validProps } = props;

    // Create a proper accessible image mock without using <img> directly
    return (
      <span className="next-image-mock" data-testid="mock-image">
        {/* We only pass valid props to avoid React warnings */}
        <span data-src={props.src} data-alt={props.alt} {...validProps} />
      </span>
    );
  },
}));

/**
 * Unit tests for the AuthenticationForm component.
 */
describe('AuthenticationForm Component', () => {
  /**
   * Test that the component renders without errors.
   */
  test('renders without crashing', () => {
    render(
      <AuthenticationForm>
        <div>Test Content</div>
      </AuthenticationForm>
    );

    // Check if the component rendered
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  /**
   * Test that the component correctly renders the MartyChat logo.
   */
  test('renders MartyChat logo', () => {
    render(
      <AuthenticationForm>
        <div>Test Content</div>
      </AuthenticationForm>
    );

    // Check if the logo is rendered - now using our mock implementation
    const logo = screen.getByTestId('mock-image');
    expect(logo).toBeInTheDocument();
    expect(logo.querySelector('span')).toHaveAttribute('data-alt', 'MartyChat Logo');
    expect(logo.querySelector('span')).toHaveAttribute(
      'data-src',
      'https://martychat-assets-png.s3.amazonaws.com/MartyChat_Full-833x200.png'
    );
  });

  /**
   * Test that the component's logo links back to the home page.
   */
  test('logo links to home page', () => {
    render(
      <AuthenticationForm>
        <div>Test Content</div>
      </AuthenticationForm>
    );

    // Check if the logo link points to home page
    const logoLink = screen.getByRole('link');
    expect(logoLink).toHaveAttribute('href', '/');
  });

  /**
   * Test that the component correctly renders child components.
   */
  test('renders child components', () => {
    render(
      <AuthenticationForm>
        <h1>Login Form</h1>
        <input placeholder="Email" />
        <button>Submit</button>
      </AuthenticationForm>
    );

    // Check if child components are rendered
    expect(screen.getByText('Login Form')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
  });

  /**
   * Test that the component has the correct styling classes.
   */
  test('has correct styling classes', () => {
    const { container } = render(
      <AuthenticationForm>
        <div>Test Content</div>
      </AuthenticationForm>
    );

    // Check if the authentication form container has the correct classes
    const formContainer = container.querySelector('#authentication-form');
    expect(formContainer).toHaveClass('p-8');
    expect(formContainer).toHaveClass('rounded-lg');
    expect(formContainer).toHaveClass('shadow-lg');
    expect(formContainer).toHaveClass('auth-form-text');
  });

  /**
   * Test that the component maintains the correct structure.
   */
  test('maintains correct DOM structure', () => {
    const { container } = render(
      <AuthenticationForm>
        <div data-testid="form-content">Form Content</div>
      </AuthenticationForm>
    );

    // Check the overall structure
    expect(container.firstChild).toHaveClass('h-screen');

    // Check if the layout has flex container
    const flexContainer = container.querySelector('.flex.flex-col.items-center');
    expect(flexContainer).toBeInTheDocument();

    // Verify logo and form are in the correct order
    const elements = flexContainer.children;
    expect(elements[0]).toContainElement(screen.getByTestId('mock-image'));
    expect(elements[1]).toContainElement(screen.getByTestId('form-content'));
  });
});
