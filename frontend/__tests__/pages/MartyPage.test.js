/**
 * @fileoverview Unit tests for the Marty Page component in MartyChat.
 * These tests validate rendering and configuration of the chat interface.
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
import MartyPage from '@/app/marty/page';
import ChatInterface from '@/components/ChatInterface';
import { martyConfig } from '@/chatbots/marty';

// Mock the ChatInterface component
jest.mock('@/components/ChatInterface', () => {
  const MockChatInterface = (props) => (
    <div data-testid="chat-interface-mock" data-props={JSON.stringify(props)}>
      Mock Chat Interface
    </div>
  );
  MockChatInterface.displayName = 'ChatInterface';
  return MockChatInterface;
});

/**
 * Unit tests for the MartyPage component.
 */
describe('MartyPage Component', () => {
  /**
   * Test that the component renders without errors.
   */
  test('renders without crashing', () => {
    render(<MartyPage />);

    // Check if the mocked ChatInterface is rendered
    expect(screen.getByTestId('chat-interface-mock')).toBeInTheDocument();
    expect(screen.getByText('Mock Chat Interface')).toBeInTheDocument();
  });

  /**
   * Test that the component passes correct configuration to ChatInterface.
   */
  test('passes correct configuration to ChatInterface', () => {
    render(<MartyPage />);

    // Get the props passed to ChatInterface
    const chatInterfaceProps = JSON.parse(screen.getByTestId('chat-interface-mock').getAttribute('data-props'));

    // Verify props match martyConfig
    expect(chatInterfaceProps.title).toBe(martyConfig.title);
    expect(chatInterfaceProps.endpoint).toBe(martyConfig.endpoint);
    expect(chatInterfaceProps.placeholder).toBe(martyConfig.placeholder);
    expect(chatInterfaceProps.welcomeMessage).toBe(martyConfig.welcomeMessage);
  });

  /**
   * Test that the martyConfig has expected values.
   */
  test('martyConfig has expected values', () => {
    // Verify martyConfig has the expected structure and values
    expect(martyConfig).toHaveProperty('title', 'Marty - Your Psychology Research Assistant');
    expect(martyConfig).toHaveProperty('endpoint', '/api/v1/marty');
    expect(martyConfig).toHaveProperty('placeholder', 'Ask Marty about psychology...');
    expect(martyConfig).toHaveProperty(
      'welcomeMessage',
      "Hello! I'm Marty, your psychology research assistant. How can I help you today?"
    );
  });

  /**
   * Test that the component spreads all martyConfig properties to ChatInterface.
   */
  test('spreads all martyConfig properties to ChatInterface', () => {
    render(<MartyPage />);

    // Get the props passed to ChatInterface
    const chatInterfaceProps = JSON.parse(screen.getByTestId('chat-interface-mock').getAttribute('data-props'));

    // Check that all properties from martyConfig are passed to ChatInterface
    Object.entries(martyConfig).forEach(([key, value]) => {
      expect(chatInterfaceProps[key]).toBe(value);
    });
  });
});
