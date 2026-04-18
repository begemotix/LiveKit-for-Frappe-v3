'use client';

import { useState, useCallback } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Mic, Send } from 'lucide-react';
import { VoiceVisualizer } from './VoiceVisualizer';
import { LiveKitProvider } from '@/components/LiveKitProvider';
import { useVoiceAssistant, useRoomContext } from '@livekit/components-react';
import useChatAndTranscription from '@/hooks/use-chat-and-transcription';
import { cn } from '@/lib/utils';

interface ChatPanelProps {
  isOpen: boolean;
}

const ChatPanelContent = () => {
  const { state: agentState } = useVoiceAssistant();
  const { messages } = useChatAndTranscription();
  
  const statusLabel = {
    disconnected: 'Bereit für Gespräch',
    connecting: 'Verbindung wird aufgebaut...',
    listening: 'Agent hört zu...',
    thinking: 'Agent denkt nach...',
    speaking: 'Agent spricht...',
  }[agentState] || 'Bereit';

  return (
    <>
      <CardHeader className="border-b bg-muted/30 p-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[18px] font-semibold">LiveKit Voice Assistant</CardTitle>
          <div className="flex items-center gap-2">
            <div className={cn(
              "size-2 rounded-full",
              agentState === 'disconnected' ? "bg-muted-foreground" : "bg-green-500 animate-pulse"
            )} />
            <span className="text-xs text-muted-foreground">{statusLabel}</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 p-4 overflow-hidden flex flex-col gap-4">
        <ScrollArea className="flex-1 pr-4">
          <div className="flex flex-col space-y-4">
            {messages.length === 0 ? (
              <div className="rounded-lg bg-muted p-3 text-sm italic text-muted-foreground">
                Willkommen! Drücken Sie unten auf den Button, um das Gespräch zu starten.
              </div>
            ) : (
              messages.map((msg, i) => (
                <div key={i} className={cn(
                  "flex flex-col max-w-[80%] rounded-lg p-3 text-sm",
                  msg.from?.isLocal 
                    ? "ml-auto bg-primary text-primary-foreground" 
                    : "mr-auto bg-muted text-foreground"
                )}>
                  <span className="font-bold text-[10px] uppercase opacity-50 mb-1">
                    {msg.from?.isLocal ? 'Du' : 'Agent'}
                  </span>
                  {msg.message}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
        
        {/* Voice-Visualizer immer anzeigen, wenn verbunden */}
        <VoiceVisualizer />
      </CardContent>

      <CardFooter className="border-t p-4">
        {/* In diesem Widget fokussieren wir auf Voice, aber Text wäre auch möglich */}
        <Button variant="outline" className="w-full" onClick={() => window.location.reload()}>
          Gespräch beenden
        </Button>
      </CardFooter>
    </>
  );
};

export const ChatPanel = ({ isOpen }: ChatPanelProps) => {
  const [token, setToken] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const startConversation = useCallback(async () => {
    setIsConnecting(true);
    try {
      const response = await fetch('/api/token');
      const data = await response.json();
      setToken(data.token);
    } catch (error) {
      console.error('Failed to fetch token:', error);
    } finally {
      setIsConnecting(false);
    }
  }, []);

  if (!isOpen) return null;

  return (
    <Card className="fixed bottom-24 right-6 z-50 flex h-[600px] w-[400px] flex-col overflow-hidden shadow-2xl animate-in slide-in-from-bottom-5 duration-300">
      {!token ? (
        <>
          <CardHeader className="border-b bg-muted/30 p-4">
            <CardTitle className="text-[18px] font-semibold">LiveKit Voice Assistant</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-4 flex flex-col items-center justify-center text-center">
            <Mic className="size-12 mb-4 opacity-20" />
            <h3 className="text-lg font-medium mb-2">Bereit für ein Gespräch?</h3>
            <p className="text-sm text-muted-foreground mb-6">
              Klicken Sie auf den Button unten, um eine Echtzeit-Verbindung mit dem Agenten aufzubauen.
            </p>
          </CardContent>
          <CardFooter className="border-t p-4">
            <Button 
              className="w-full" 
              onClick={startConversation}
              disabled={isConnecting}
            >
              {isConnecting ? 'Verbindung wird aufgebaut...' : 'Gespräch starten'}
            </Button>
          </CardFooter>
        </>
      ) : (
        <LiveKitProvider 
          token={token} 
          serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
          connect={true}
        >
          <ChatPanelContent />
        </LiveKitProvider>
      )}
    </Card>
  );
};
