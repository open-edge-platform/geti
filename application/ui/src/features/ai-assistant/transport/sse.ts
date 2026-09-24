// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const consumeSse = async (
    body: ReadableStream<Uint8Array>,
    onData: (payload: string) => void
): Promise<void> => {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
        for (;;) {
            const { done, value } = await reader.read();
            buffer += decoder.decode(value, { stream: !done });

            let boundary = /\r?\n\r?\n/.exec(buffer);
            while (boundary !== null) {
                const event = buffer.slice(0, boundary.index);
                buffer = buffer.slice(boundary.index + boundary[0].length);
                event
                    .split(/\r?\n/)
                    .filter((line) => line.startsWith('data:'))
                    .forEach((line) => onData(line.slice(5).trim()));
                boundary = /\r?\n\r?\n/.exec(buffer);
            }

            if (done) break;
        }
    } finally {
        void reader.cancel();
    }
};
