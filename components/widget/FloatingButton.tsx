'use client';

import { MessageCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface FloatingButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

export const FloatingButton = ({ isOpen, onClick }: FloatingButtonProps) => {
  return (
    <Button
      variant="primary"
      size="icon"
      className={cn(
        'fixed right-6 bottom-6 z-50 size-14 rounded-full shadow-lg transition-all duration-300 hover:scale-110 active:scale-95',
        isOpen ? 'rotate-90' : 'rotate-0'
      )}
      onClick={onClick}
      aria-label={isOpen ? 'Chat schließen' : 'Chat öffnen'}
    >
      {isOpen ? <X className="size-6" /> : <MessageCircle className="size-6" />}
    </Button>
  );
};
