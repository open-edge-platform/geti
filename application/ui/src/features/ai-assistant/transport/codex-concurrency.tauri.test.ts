// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { waitFor } from '@testing-library/react';

import type { StreamRequest } from '../types';

const { invokeMock, connection } = vi.hoisted(() => ({
    invokeMock: vi.fn(),
    connection: { executable: '' },
}));
vi.mock('@tauri-apps/api/core', () => ({ invoke: invokeMock, Channel: class {} }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openUrl: vi.fn() }));
vi.mock('../connection', () => ({ getAiConnection: () => connection }));

const deferred = () => {
    let resolve!: (value: unknown) => void;
    const promise = new Promise<unknown>((done) => {
        resolve = done;
    });
    return { promise, resolve };
};
const signedIn = { account: { type: 'chatgpt', email: 'test@example.com', planType: 'plus' } };
const request = (requestId: string): StreamRequest => ({
    requestId,
    model: '',
    instructions: '',
    input: [],
    tools: [],
    onDelta: vi.fn(),
});
let transport: typeof import('./codex-transport.tauri');

beforeEach(async () => {
    vi.resetModules();
    invokeMock.mockReset();
    connection.executable = '';
    transport = await import('./codex-transport.tauri');
});

it('shares concurrent account probes and reuses confirmed sign-in when a drawer reopens', async () => {
    const status = deferred();
    invokeMock.mockReturnValue(status.promise);
    const first = transport.codexStatus();
    const second = transport.codexStatus();
    await waitFor(() => expect(invokeMock).toHaveBeenCalledTimes(1));
    status.resolve(signedIn);
    expect(await first).toEqual(await second);
    expect(await transport.codexStatus()).toEqual({ email: 'test@example.com', plan: 'plus' });
    expect(invokeMock).toHaveBeenCalledTimes(1);
});

it('serializes model discovery, chat and status through the same native queue', async () => {
    const models = deferred();
    invokeMock
        .mockReturnValueOnce(models.promise)
        .mockResolvedValueOnce({ text: 'Hello', calls: [] })
        .mockResolvedValueOnce(signedIn);
    const lookup = transport.codexModels();
    const reply = transport.codexRespond(request('reply'));
    const status = transport.codexStatus();
    await waitFor(() => expect(invokeMock).toHaveBeenCalledTimes(1));
    models.resolve({ data: [] });
    await Promise.all([lookup, reply, status]);
    expect(invokeMock.mock.calls.map(([, args]) => args.operation)).toEqual(['models', 'response', 'status']);
});

it('cancels a queued response immediately without starting a native operation', async () => {
    const models = deferred();
    invokeMock.mockReturnValue(models.promise);
    const lookup = transport.codexModels();
    const reply = transport.codexRespond(request('queued'));
    const stopped = expect(reply).rejects.toThrow('Stopped');
    transport.codexCancel('queued');
    await stopped;
    models.resolve({ data: [] });
    await lookup;
    await transport.codexModels();
    expect(invokeMock.mock.calls.map(([, args]) => args.operation)).toEqual(['models', 'models']);
});

it('keeps the native slot occupied until a cancelled response actually settles', async () => {
    const response = deferred();
    invokeMock.mockImplementation((command) => (command === 'codex_cancel' ? Promise.resolve() : response.promise));
    const reply = transport.codexRespond(request('active'));
    await waitFor(() => expect(invokeMock).toHaveBeenCalledTimes(1));
    const stopped = expect(reply).rejects.toThrow('Stopped');
    transport.codexCancel('active');
    await stopped;
    const models = transport.codexModels();
    expect(invokeMock.mock.calls.map(([command]) => command)).toEqual(['codex_operation', 'codex_cancel']);
    response.resolve({ text: '', calls: [], data: [] });
    await models;
    expect(invokeMock.mock.calls.at(-1)?.[1].operation).toBe('models');
});

it('waits for login before probing the account and prevents duplicate login windows', async () => {
    invokeMock.mockResolvedValueOnce({ account: null });
    expect(await transport.codexStatus()).toBeNull();
    const login = deferred();
    invokeMock.mockReturnValueOnce(login.promise).mockResolvedValueOnce(signedIn);
    const first = transport.codexLogin(vi.fn());
    const second = transport.codexLogin(vi.fn());
    const status = transport.codexStatus();
    await waitFor(() => expect(invokeMock).toHaveBeenCalledTimes(2));
    login.resolve({});
    await Promise.all([first, second]);
    expect(await status).toMatchObject({ email: 'test@example.com' });
    expect(invokeMock.mock.calls.map(([, args]) => args.operation)).toEqual(['status', 'login', 'status']);
});

it('clears the cached account after a successful logout', async () => {
    invokeMock.mockResolvedValueOnce(signedIn).mockResolvedValueOnce({});
    await transport.codexStatus();
    await transport.codexLogout();
    expect(await transport.codexStatus()).toBeNull();
    expect(invokeMock).toHaveBeenCalledTimes(2);
});

it('does not replace a confirmed account with a transient probe failure', async () => {
    invokeMock.mockResolvedValueOnce(signedIn).mockRejectedValueOnce('Connection closed');
    await transport.codexStatus();
    await expect(transport.codexStatus(true)).rejects.toThrow('Connection closed');
    expect(await transport.codexStatus()).toMatchObject({ email: 'test@example.com' });
    expect(invokeMock).toHaveBeenCalledTimes(2);
});

it('does not reuse a different executable profile or let its late probe overwrite the current profile', async () => {
    const oldStatus = deferred();
    invokeMock.mockReturnValueOnce(oldStatus.promise).mockResolvedValueOnce({ account: null });
    const old = transport.codexStatus();
    await waitFor(() => expect(invokeMock).toHaveBeenCalledTimes(1));
    connection.executable = 'other-codex.exe';
    const current = transport.codexStatus();
    oldStatus.resolve(signedIn);
    await old;
    expect(await current).toBeNull();
    expect(await transport.codexStatus()).toBeNull();
    expect(invokeMock.mock.calls[1][1].executable).toBe('other-codex.exe');
});

it('recognizes a signed-in ChatGPT account without an email field', async () => {
    invokeMock.mockResolvedValue({ account: { type: 'chatgpt', planType: 'plus' } });
    expect(await transport.codexStatus()).toEqual({ email: null, plan: 'plus' });
});
