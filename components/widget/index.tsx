'use client';

import { useState } from 'react';
import { FloatingButton } from './FloatingButton';
import { ChatPanel } from './ChatPanel';

export const VoiceWidget = () => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleWidget = () => {
    setIsOpen((prev) => !prev);
  };

  return (
    <div className="voice-widget">
      <ChatPanel isOpen={isOpen} />
      <FloatingButton isOpen={isOpen} onClick={toggleWidget} />
    </div>
  );
};
