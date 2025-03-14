/**
 * @fileoverview Chat Interface for the user to interact with the Marty chatbot.
 * This file contains the main logic for the marty chat interface.
 *
 * @author Nikolai Alexander
 * @email njalexander93@gmail.com
 * @version 1.0.0
 * @date 2025-02-28
 * @license Proprietary
 * @copyright Copyright (c) 2025 MartyChat
 */

'use client';

import { useEffect, useState } from 'react';
import ChatInterface from '@/components/ChatInterface';
import { martyConfig } from '@/chatbots/marty';

/**
 * The Marty chat interface component.
 *
 * @returns {React.Element} The rendered signup page component.
 */
export default function MartyPage() {
  return <ChatInterface {...martyConfig} />;
}
