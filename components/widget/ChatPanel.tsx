'use client';

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Mic } from 'lucide-react';

interface ChatPanelProps {
  isOpen: boolean;
}

export const ChatPanel = ({ isOpen }: ChatPanelProps) => {
  if (!isOpen) return null;

  return (
    <Card className="fixed bottom-24 right-6 z-50 flex h-[600px] w-[400px] flex-col overflow-hidden shadow-2xl animate-in slide-in-from-bottom-5 duration-300">
      <CardHeader className="border-b bg-muted/30 p-4">
        <CardTitle className="text-[18px] font-semibold">LiveKit Voice Assistant</CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 p-4">
        <ScrollArea className="h-full">
          <div className="flex flex-col space-y-4">
            {/* Platzhalter für Nachrichten-Historie */}
            <div className="rounded-lg bg-muted p-3 text-sm italic text-muted-foreground">
              Willkommen! Drücken Sie unten auf den Button, um das Gespräch zu starten.
            </div>
            
            {/* Platzhalter für Voice-Visualizer */}
            <div className="flex h-32 items-center justify-center rounded-lg border-2 border-dashed border-muted">
              <div className="flex flex-col items-center space-y-2 text-muted-foreground">
                <Mic className="size-8 opacity-20" />
                <span className="text-xs">Visualizer Placeholder</span>
              </div>
            </div>
          </div>
        </ScrollArea>
      </CardContent>

      <CardFooter className="border-t p-4">
        <Button variant="primary" className="w-full" onClick={() => console.log('Start conversation')}>
          Gespräch starten
        </Button>
      </CardFooter>
    </Card>
  );
};
