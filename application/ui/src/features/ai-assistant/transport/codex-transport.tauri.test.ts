// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { beforeEach, describe, expect, it, vi } from 'vitest';

import { codexDiagnostics, codexLogin, codexStatus } from './codex-transport.tauri';

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }));

vi.mock('@tauri-apps/api/core', () => ({
    invoke: invokeMock,
    Channel: class {},
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openUrl: vi.fn() }));

describe('Codex desktop connection errors', () => {
    beforeEach(() => {
        invokeMock.mockReset();
    });

    it.each([
        ['status', codexStatus],
        ['login', () => codexLogin(vi.fn())],
        ['diagnostics', codexDiagnostics],
    ])('preserves Rust error details for %s', async (_operation, action) => {
        const message = 'Could not resolve the ChatGPT storage path: Access is denied.';
        invokeMock.mockRejectedValue(message);

        await expect(action()).rejects.toThrow(message);
    });

    it('preserves an existing JavaScript Error', async () => {
        const error = new Error('Connection closed');
        invokeMock.mockRejectedValue(error);

        await expect(codexStatus()).rejects.toBe(error);
    });

    it('returns a signed-out account without treating it as a connection error', async () => {
        invokeMock.mockResolvedValue({ account: null, requiresOpenaiAuth: true });

        await expect(codexStatus()).resolves.toBeNull();
    });
});
