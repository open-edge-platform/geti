// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { act, renderHook, waitFor } from '@testing-library/react';

import { useConnectionStatus } from './use-connection-status';

const { status, connection } = vi.hoisted(() => ({
    status: vi.fn(),
    connection: { provider: 'chatgpt', executable: '' },
}));
vi.mock('../connection', () => ({ useAiConnection: () => connection }));
vi.mock('../transport/codex-transport', () => ({ codexStatus: status }));
vi.mock('../transport/key-service', () => ({ hasStoredKey: async () => false }));

beforeEach(() => {
    status.mockReset();
    connection.executable = '';
});

it('keeps confirmed sign-in on a failed refresh, but clears it on an authoritative signed-out result', async () => {
    status
        .mockResolvedValueOnce({ email: 'test@example.com', plan: 'plus' })
        .mockRejectedValueOnce(new Error('Temporary connection error'))
        .mockResolvedValueOnce(null);
    const { result } = renderHook(useConnectionStatus);
    await waitFor(() => expect(result.current.isReady).toBe(true));
    act(() => result.current.refresh());
    await waitFor(() => expect(result.current.error).toBe('Temporary connection error'));
    expect(result.current.isReady).toBe(true);
    act(() => result.current.refresh());
    await waitFor(() => expect(result.current.isReady).toBe(false));
    expect(result.current.error).toBeNull();
});

it('checks a changed executable without preserving the old profile account', async () => {
    status
        .mockResolvedValueOnce({ email: 'test@example.com', plan: 'plus' })
        .mockRejectedValueOnce(new Error('Not found'));
    const { result, rerender } = renderHook(useConnectionStatus);
    await waitFor(() => expect(result.current.isReady).toBe(true));
    connection.executable = 'different.exe';
    rerender();
    await waitFor(() => expect(result.current.error).toBe('Not found'));
    expect(result.current.account).toBeNull();
});
