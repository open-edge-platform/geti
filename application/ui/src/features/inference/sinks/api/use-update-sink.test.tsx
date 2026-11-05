// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';
import { QueryClient } from '@tanstack/react-query';
import { act, screen, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { createQueryClient } from '../../../../query-client/query-client';
import { useUpdateSink } from './use-update-sink';

const mockedSink: LocalFolderSinkConfig = {
    id: 'sink-id',
    name: 'Mock Sink',
    output_formats: [],
    sink_type: 'folder',
    folder_path: './folder/111',
};

const variables = {
    params: { path: { sink_id: 'sink-id' } },
    body: { name: 'Mock Sink', output_formats: [], folder_path: './folder/111' },
};

describe('useUpdateSink', () => {
    it('updates a sink, shows success toast, invalidates the sink query and tests the connection once', async () => {
        const testSinkSpy = rs.fn();
        server.use(
            http.patch('/api/sinks/{sink_id}', () => HttpResponse.json(mockedSink)),
            http.post('/api/sinks/{sink_id}:test', () => {
                testSinkSpy();

                return HttpResponse.json({ reachable: true, latency_ms: 5, error: null });
            })
        );

        const queryClient: QueryClient = createQueryClient();
        const invalidateSpy = rs.spyOn(queryClient, 'invalidateQueries');
        const { result } = renderHook(() => useUpdateSink(), { queryClient });

        await act(async () => {
            await result.current.mutateAsync(variables);
        });

        expect(await screen.findByLabelText('toast')).toHaveTextContent('Sink configuration updated successfully.');
        expect(invalidateSpy).toHaveBeenCalledWith({
            queryKey: ['get', '/api/sinks/{sink_id}', { params: { path: { sink_id: 'sink-id' } } }],
        });
        await waitFor(() => expect(testSinkSpy).toHaveBeenCalledTimes(1));
    });

    it('shows a single error toast with details on failure', async () => {
        server.use(
            http.patch('/api/sinks/{sink_id}', () => HttpResponse.json({ detail: 'Boom' } as never, { status: 500 }))
        );

        const { result } = renderHook(() => useUpdateSink());

        await act(async () => {
            await result.current.mutateAsync(variables).catch(() => undefined);
        });

        const toasts = await screen.findAllByLabelText('toast');

        expect(toasts).toHaveLength(1);
        expect(toasts[0]).toHaveTextContent('Failed to save sink configuration, Boom');
    });
});
