// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { consumeSse } from './sse';

const stream = (...chunks: string[]): ReadableStream<Uint8Array> => {
    const encoder = new TextEncoder();

    return new ReadableStream({
        start(controller) {
            chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)));
            controller.close();
        },
    });
};

it('consumes CRLF-delimited events split across chunks', async () => {
    const payloads: string[] = [];

    await consumeSse(stream('data: first\r\n\r', '\ndata: second\r\n\r\n'), (payload) => payloads.push(payload));

    expect(payloads).toEqual(['first', 'second']);
});

it('handles a rejected reader cleanup after the stream is aborted', async () => {
    const body = {
        getReader: () => ({
            read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
            cancel: vi.fn().mockRejectedValue(new DOMException('BodyStreamBuffer was aborted', 'AbortError')),
        }),
    } as unknown as ReadableStream<Uint8Array>;

    await expect(consumeSse(body, vi.fn())).resolves.toBeUndefined();
});
