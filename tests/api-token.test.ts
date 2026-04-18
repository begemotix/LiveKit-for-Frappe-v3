/**
 * @vitest-environment node
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { POST } from '../app/api/token/route';

describe('API Token Route', () => {
  beforeEach(() => {
    vi.stubEnv('LIVEKIT_API_KEY', 'test_key');
    vi.stubEnv('LIVEKIT_API_SECRET', 'test_secret');
  });

  it('should generate a token for POST requests', async () => {
    const req = new Request('http://localhost/api/token', {
      method: 'POST',
    });

    const response = await POST(req);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.token).toBeDefined();
    expect(data.identity).toContain('guest-');
  });

  it('should return 500 if environment variables are missing', async () => {
    vi.stubEnv('LIVEKIT_API_KEY', '');
    vi.stubEnv('LIVEKIT_API_SECRET', '');

    const req = new Request('http://localhost/api/token', {
      method: 'POST',
    });

    const response = await POST(req);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe('Server configuration error');
  });
});
