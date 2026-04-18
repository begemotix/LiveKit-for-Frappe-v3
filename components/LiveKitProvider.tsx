'use client';

import { ReactNode } from 'react';
import { LiveKitRoom } from '@livekit/components-react';

interface LiveKitProviderProps {
  children: ReactNode;
  token: string | undefined;
  serverUrl: string | undefined;
  connect?: boolean;
}

export function LiveKitProvider({
  children,
  token,
  serverUrl,
  connect = false,
}: LiveKitProviderProps) {
  if (!token || !serverUrl) {
    return <>{children}</>;
  }

  return (
    <LiveKitRoom token={token} serverUrl={serverUrl} connect={connect} audio={true} video={false}>
      {children}
    </LiveKitRoom>
  );
}
