// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { StreamRequest } from '../types';

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }));

vi.mock('@tauri-apps/api/core', () => ({
    invoke: invokeMock,
    Channel: class {
        onmessage?: (event: unknown) => void;
    },
}));
vi.mock('../platform', () => ({ hasSecureAiBackend: () => true }));
vi.mock('../connection', () => ({
    getAiConnection: () => ({ agentId: 'anthropic-app', executable: '', model: 'sonnet' }),
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));

const request = (requestId: string): StreamRequest => ({
    requestId,
    model: 'sonnet',
    instructions: 'Annotate.',
    input: [],
    tools: [],
    onDelta: vi.fn(),
});

beforeEach(() => {
    invokeMock.mockReset();
});

it('assembles Anthropic text and tool calls from native SSE events', async () => {
    invokeMock.mockImplementation(async (_command, args) => {
        args.onEvent.onmessage({
            type: 'sse',
            data: JSON.stringify({ type: 'content_block_start', index: 0, content_block: { type: 'text' } }),
        });
        args.onEvent.onmessage({
            type: 'sse',
            data: JSON.stringify({
                type: 'content_block_delta',
                index: 0,
                delta: { type: 'text_delta', text: 'Done' },
            }),
        });
        args.onEvent.onmessage({
            type: 'sse',
            data: JSON.stringify({
                type: 'content_block_start',
                index: 1,
                content_block: { type: 'tool_use', id: 'call-1', name: 'propose_annotations' },
            }),
        });
        args.onEvent.onmessage({
            type: 'sse',
            data: JSON.stringify({
                type: 'content_block_delta',
                index: 1,
                delta: { type: 'input_json_delta', partial_json: '{"annotations":[]}' },
            }),
        });
        args.onEvent.onmessage({ type: 'sse', data: JSON.stringify({ type: 'message_stop' }) });
    });
    const { streamAnthropicResponse } = await import('./anthropic-transport.tauri');
    const pending = request('anthropic-1');

    await expect(streamAnthropicResponse(pending)).resolves.toEqual({
        text: 'Done',
        functionCalls: [{ callId: 'call-1', name: 'propose_annotations', arguments: '{"annotations":[]}' }],
    });
    expect(pending.onDelta).toHaveBeenCalledWith('Done');
});

it('uses the response request ID for Claude operations and cancellation', async () => {
    invokeMock.mockResolvedValue({ text: '', calls: [] });
    const { claudeCancel, claudeRespond } = await import('./claude-transport.tauri');

    await claudeRespond(request('claude-1'));
    claudeCancel('claude-1');

    expect(invokeMock).toHaveBeenNthCalledWith(
        1,
        'claude_operation',
        expect.objectContaining({ requestId: 'claude-1', operation: 'response' })
    );
    expect(invokeMock).toHaveBeenNthCalledWith(2, 'claude_cancel', { requestId: 'claude-1' });
});
