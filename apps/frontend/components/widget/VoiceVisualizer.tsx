'use client';

import { BarVisualizer, useVoiceAssistant } from '@livekit/components-react';
import { cn } from '@/lib/utils';

interface VoiceVisualizerProps {
  className?: string;
}

export const VoiceVisualizer = ({ className }: VoiceVisualizerProps) => {
  const { state, audioTrack } = useVoiceAssistant();

  // Hinweis: AgentAudioVisualizerWave wäre die polierte Version aus @agents-ui.
  // Wir nutzen hier den verfügbaren BarVisualizer.
  return (
    <div className={cn('bg-muted/20 flex h-32 items-center justify-center rounded-lg', className)}>
      <BarVisualizer
        state={state}
        trackRef={audioTrack}
        barCount={7}
        options={{ minHeight: 4 }}
        className="flex items-center justify-center gap-2"
        style={{ color: 'var(--widget-primary)' }}
      />
    </div>
  );
};
