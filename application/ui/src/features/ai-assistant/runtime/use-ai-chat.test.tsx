// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AnnotationTarget } from '../annotation/annotation-tools';
import type { StreamResult } from '../types';
import { useAiChat } from './use-ai-chat';

const { respond, cancel } = vi.hoisted(() => ({ respond: vi.fn(), cancel: vi.fn() }));
vi.mock('../connection', () => ({ useAiConnection: () => ({ provider: 'chatgpt', model: '' }) }));
vi.mock('../transport/codex-transport', () => ({ codexRespond: respond, codexCancel: cancel }));
const target: AnnotationTarget = {
    key: 'project/image',
    width: 100,
    height: 100,
    taskType: 'detection',
    exclusiveLabels: true,
    labels: [{ id: 'cat', name: 'Cat', color: '#ff0000' }],
    source: { id: 'image', name: 'Image', url: '/image.png' },
    apply: vi.fn(),
};
const attachment = { id: 'image', name: 'Image', dataUrl: 'data:image/png;base64,test' };
const proposal: StreamResult = {
    text: '',
    functionCalls: [
        {
            callId: 'proposal',
            name: 'propose_annotations',
            arguments: JSON.stringify({
                media_key: target.key,
                annotations: [{ label_ids: ['cat'], x: 10, y: 20, width: 30, height: 40 }],
            }),
        },
    ],
};

describe('ChatGPT annotation conversation', () => {
    beforeEach(() => {
        respond.mockReset();
        cancel.mockReset();
        vi.mocked(target.apply).mockReset();
    });

    it('sends the image and immediately applies validated annotations', async () => {
        respond
            .mockResolvedValueOnce(proposal)
            .mockResolvedValueOnce({ text: '1 Cat box added. Edit or Undo, then Submit to save.', functionCalls: [] });
        const { result } = renderHook(() => useAiChat('project', '', { target }));
        act(() => result.current.send('Annotate the cat', [attachment]));
        await waitFor(() => expect(result.current.status).toBe('idle'));
        expect(target.apply).toHaveBeenCalledExactlyOnceWith([
            expect.objectContaining({
                labels: [{ id: 'cat' }],
                shape: {
                    type: 'rectangle',
                    x: 10,
                    y: 20,
                    width: 30,
                    height: 40,
                },
            }),
        ]);
        expect(respond.mock.calls[1][0].input.at(-1)).toMatchObject({
            type: 'function_call_output',
            output: JSON.stringify({ status: 'applied_to_editor', count: 1, saved: false }),
        });
        const request = respond.mock.calls[0][0];
        expect(request.input[0].content).toContainEqual({
            type: 'input_image',
            image_url: attachment.dataUrl,
            detail: 'high',
        });
        expect(request.tools.some(({ name }: { name: string }) => name === 'propose_annotations')).toBe(true);
        expect(request.instructions).toContain('original pixel coordinates');
    });
    it('does not expose annotation tools without the current image', async () => {
        respond.mockResolvedValue({ text: 'Attach the image.', functionCalls: [] });
        const { result } = renderHook(() => useAiChat('project', '', { target }));
        act(() => result.current.send('Annotate', []));
        await waitFor(() => expect(result.current.status).toBe('idle'));
        expect(
            respond.mock.calls[0][0].tools.some(({ name }: { name: string }) => name === 'propose_annotations')
        ).toBe(false);
    });
    it('ignores late proposals after the editor closes', async () => {
        let finish!: (value: StreamResult) => void;
        respond.mockImplementation(
            () =>
                new Promise<StreamResult>((resolve) => {
                    finish = resolve;
                })
        );
        const { result, unmount } = renderHook(() => useAiChat('project', '', { target }));
        act(() => result.current.send('Annotate', [attachment]));
        unmount();
        await act(async () => {
            finish(proposal);
        });
        expect(cancel).toHaveBeenCalledOnce();
        expect(target.apply).not.toHaveBeenCalled();
    });
    it('reports malformed proposals to the model without applying any shapes', async () => {
        const invalid = {
            ...proposal,
            functionCalls: [{ ...proposal.functionCalls[0], arguments: '{"media_key":"other","annotations":[]}' }],
        };
        respond
            .mockResolvedValueOnce(invalid)
            .mockResolvedValueOnce({ text: 'Could not annotate.', functionCalls: [] });
        const { result } = renderHook(() => useAiChat('project', '', { target }));
        act(() => result.current.send('Annotate', [attachment]));
        await waitFor(() => expect(result.current.status).toBe('idle'));
        expect(target.apply).not.toHaveBeenCalled();
        expect(result.current.messages[1].toolCalls?.[0].status).toBe('error');
    });
    it('leaves annotations unchanged when no objects match', async () => {
        const empty = {
            ...proposal,
            functionCalls: [
                {
                    ...proposal.functionCalls[0],
                    arguments: JSON.stringify({
                        media_key: target.key,
                        annotations: [],
                    }),
                },
            ],
        };
        respond.mockResolvedValueOnce(empty).mockResolvedValueOnce({ text: 'No matching objects.', functionCalls: [] });
        const { result } = renderHook(() => useAiChat('project', '', { target }));
        act(() => result.current.send('Annotate', [attachment]));
        await waitFor(() => expect(result.current.status).toBe('idle'));
        expect(target.apply).not.toHaveBeenCalled();
        expect(respond.mock.calls[1][0].input.at(-1).output).toBe(
            JSON.stringify({ status: 'no_matching_objects', count: 0, saved: false })
        );
    });
    it('reports editor rejection without claiming annotations were applied', async () => {
        vi.mocked(target.apply).mockImplementationOnce(() => {
            throw new Error('The image changed.');
        });
        respond
            .mockResolvedValueOnce(proposal)
            .mockResolvedValueOnce({ text: 'Could not annotate.', functionCalls: [] });
        const { result } = renderHook(() => useAiChat('project', '', { target }));
        act(() => result.current.send('Annotate', [attachment]));
        await waitFor(() => expect(result.current.status).toBe('idle'));
        expect(result.current.messages[1].toolCalls?.[0].status).toBe('error');
        expect(respond.mock.calls[1][0].input.at(-1).output).toContain('The image changed.');
        expect(respond.mock.calls[1][0].input.at(-1).output).not.toContain('applied_to_editor');
    });
});
