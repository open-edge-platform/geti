// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';
import { act, screen, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { useCreateSink } from './use-create-sink';

const mockedSink: LocalFolderSinkConfig = {
    id: 'original-id',
    name: 'Mock Sink',
    output_formats: [],
    sink_type: 'folder',
    folder_path: './folder/111',
};

describe('useCreateSink', () => {
    it('creates a sink, shows success toast and tests the connection once', async () => {
        const testSinkSpy = rs.fn();
        server.use(
            http.post('/api/sinks', () => HttpResponse.json({ ...mockedSink, id: 'new-id' })),
            http.post('/api/sinks/{sink_id}:test', () => {
                testSinkSpy();

                return HttpResponse.json({ reachable: true, latency_ms: 5, error: null });
            })
        );

        const { result } = renderHook(() => useCreateSink());

        await act(async () => {
            await result.current.mutateAsync({ body: mockedSink });
        });

        expect(await screen.findByLabelText('toast')).toHaveTextContent('Sink configuration created successfully.');
        await waitFor(() => expect(testSinkSpy).toHaveBeenCalledTimes(1));
    });

    it('shows a single error toast with details on failure', async () => {
        server.use(
            http.post('/api/sinks', () =>
                HttpResponse.json({ detail: 'Sink already exists' } as never, { status: 409 })
            )
        );

        const { result } = renderHook(() => useCreateSink());

        await act(async () => {
            await result.current.mutateAsync({ body: mockedSink }).catch(() => undefined);
        });

        const toasts = await screen.findAllByLabelText('toast');

        expect(toasts).toHaveLength(1);
        expect(toasts[0]).toHaveTextContent('Failed to save sink configuration, Sink already exists');
    });
});
