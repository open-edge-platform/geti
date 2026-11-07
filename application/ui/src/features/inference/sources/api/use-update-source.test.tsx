// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';
import { act, screen, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { createQueryClient, getQueryKey } from '../../../../query-client/query-client';
import { useUpdateSource } from './use-update-source';

const source: IPCameraSourceConfig = {
    id: 'source-id',
    name: 'Camera',
    source_type: 'ip_camera',
    stream_url: 'rtsp://camera/stream',
    auth_required: false,
};

const variables = { params: { path: { source_id: source.id } }, body: { name: 'Renamed' } };

describe('useUpdateSource', () => {
    it('shows success toast, invalidates the single source and requests the source test once', async () => {
        const queryClient = createQueryClient();
        const invalidateSpy = rs.spyOn(queryClient, 'invalidateQueries');
        const testSourceSpy = rs.fn();
        server.use(
            http.patch('/api/sources/{source_id}', () => HttpResponse.json(source)),
            http.post('/api/sources/{source_id}:test', () => {
                testSourceSpy();

                return HttpResponse.json({ reachable: true, latency_ms: 10, error: null });
            })
        );

        const { result } = renderHook(() => useUpdateSource(), { queryClient });

        await act(async () => {
            await result.current.mutateAsync(variables);
        });

        await waitFor(() => {
            expect(screen.getByText('Source configuration updated successfully.')).toBeVisible();
            expect(testSourceSpy).toHaveBeenCalledTimes(1);
            expect(invalidateSpy).toHaveBeenCalledWith({
                queryKey: getQueryKey([
                    'get',
                    '/api/sources/{source_id}',
                    { params: { path: { source_id: source.id } } },
                ]),
            });
        });
    });

    it('shows error toast with details when updating fails', async () => {
        server.use(
            http.patch('/api/sources/{source_id}', () =>
                HttpResponse.json({ detail: 'bad url' } as never, { status: 400 })
            )
        );

        const { result } = renderHook(() => useUpdateSource());

        await act(async () => {
            await result.current.mutateAsync(variables).catch(() => undefined);
        });

        await waitFor(() => {
            expect(screen.getByText('Failed to save source configuration, bad url')).toBeVisible();
        });
    });
});
