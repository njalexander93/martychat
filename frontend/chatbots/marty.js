/**
 * @fileoverview Chat interface configuration for Marty.
 * This file defines the configuration for the ChatInterface.js component for the Marty chatbot.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date TBD
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */


export const martyConfig = {
  title: "Marty - Your Psychology Research Assistant",
  endpoint: "/api/v1/marty",
  placeholder: "Ask me about psychology...",
  welcomeMessage: "Hello! I'm Marty, your psychology research assistant. How can I help you today?",
  maxInputLines: 18,
  theme: {
    primary: 'primary',
    userMessage: 'bg-primary text-text-light',
    botMessage: 'bg-bg-secondary text-text-primary',
    fonts: {
      title: 'font-roboto-slab',
      messages: 'font-roboto',
      input: 'font-roboto-flex'
    },
    container: {
      background: 'bg-transparent border-transparent',
      input: 'bg-transparent border-transparent'
    }
  }
};
