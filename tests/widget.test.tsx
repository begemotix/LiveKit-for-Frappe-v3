import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LiveKitProvider } from '../components/LiveKitProvider';
import React from 'react';

// Mock LiveKitRoom to avoid WebRTC issues in tests
vi.mock('@livekit/components-react', () => ({
  LiveKitRoom: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="livekit-room">{children}</div>
  ),
}));

describe('LiveKitProvider', () => {
  it('renders children even without token/url', () => {
    const { getByText, queryByTestId } = render(
      <LiveKitProvider token={undefined} serverUrl={undefined}>
        <div>Test Child</div>
      </LiveKitProvider>
    );

    expect(getByText('Test Child')).toBeDefined();
    expect(queryByTestId('livekit-room')).toBeNull();
  });

  it('renders LiveKitRoom when token and url are provided', () => {
    const { getByTestId, getByText } = render(
      <LiveKitProvider token="test-token" serverUrl="ws://localhost:7880">
        <div>Test Child</div>
      </LiveKitProvider>
    );

    expect(getByTestId('livekit-room')).toBeDefined();
    expect(getByText('Test Child')).toBeDefined();
  });
});
