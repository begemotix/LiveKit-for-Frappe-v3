'use client';

import { useCallback, useState } from 'react';
import { Mic } from 'lucide-react';
import { useVoiceAssistant } from '@livekit/components-react';
import { LiveKitProvider } from '@/components/LiveKitProvider';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import useChatAndTranscription from '@/hooks/use-chat-and-transcription';
import { cn } from '@/lib/utils';
import { VoiceVisualizer } from './VoiceVisualizer';

interface ChatPanelProps {
  isOpen: boolean;
}

const ChatPanelContent = () => {
  const { state: agentState } = useVoiceAssistant();
  const { messages } = useChatAndTranscription();

  const statusMap: Record<string, string> = {
    disconnected: 'Bereit für Gespräch',
    connecting: 'Verbindung wird aufgebaut...',
    initializing: 'Agent initialisiert...',
    listening: 'Agent hört zu...',
    thinking: 'Agent denkt nach...',
    speaking: 'Agent spricht...',
  };
  const statusLabel = statusMap[agentState] || 'Bereit';

  return (
    <>
      <CardHeader className="bg-muted/30 border-b p-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[18px] font-semibold">LiveKit Voice Assistant</CardTitle>
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'size-2 rounded-full',
                agentState === 'disconnected' ? 'bg-muted-foreground' : 'animate-pulse bg-green-500'
              )}
            />
            <span className="text-muted-foreground text-xs">{statusLabel}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col gap-4 overflow-hidden p-4">
        <ScrollArea className="flex-1 pr-4">
          <div className="flex flex-col space-y-4">
            {messages.length === 0 ? (
              <div className="bg-muted text-muted-foreground rounded-lg p-3 text-sm italic">
                Willkommen! Drücken Sie unten auf den Button, um das Gespräch zu starten.
              </div>
            ) : (
              messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex max-w-[80%] flex-col rounded-lg p-3 text-sm',
                    msg.from?.isLocal
                      ? 'bg-primary text-primary-foreground ml-auto'
                      : 'bg-muted text-foreground mr-auto'
                  )}
                >
                  <span className="mb-1 text-[10px] font-bold uppercase opacity-50">
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
  const [isGdprAccepted, setIsGdprAccepted] = useState(false);

  const gdprNotice =
    'Ich stimme zu, dass meine Voice-Daten zur Verarbeitung an den KI-Dienst übertragen werden.';

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
    <Card className="animate-in slide-in-from-bottom-5 fixed right-6 bottom-24 z-50 flex h-[600px] w-[400px] flex-col overflow-hidden shadow-2xl duration-300">
      {!token ? (
        <>
          <CardHeader className="bg-muted/30 border-b p-4">
            <CardTitle className="text-[18px] font-semibold">LiveKit Voice Assistant</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-1 flex-col items-center justify-center p-4 text-center">
            <Mic className="mb-4 size-12 opacity-20" />
            <h3 className="mb-2 text-lg font-medium">Bereit für ein Gespräch?</h3>
            <p className="text-muted-foreground mb-6 text-sm">
              Klicken Sie auf den Button unten, um eine Echtzeit-Verbindung mit dem Agenten
              aufzubauen.
            </p>

            <div className="mb-6 flex items-start space-x-3 text-left">
              <input
                type="checkbox"
                id="gdpr-checkbox"
                checked={isGdprAccepted}
                onChange={(e) => setIsGdprAccepted(e.target.checked)}
                className="accent-primary mt-1 h-4 w-4 shrink-0 rounded border-gray-300"
              />
              <label
                htmlFor="gdpr-checkbox"
                className="text-muted-foreground cursor-pointer text-xs leading-snug select-none"
              >
                {gdprNotice}
              </label>
            </div>
          </CardContent>
          <CardFooter className="border-t p-4">
            <Button
              className="w-full"
              onClick={startConversation}
              disabled={isConnecting || !isGdprAccepted}
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
