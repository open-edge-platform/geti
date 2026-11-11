// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';
import { act, screen, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { useCreateSource } from './use-create-source';

const body: Omit<IPCameraSourceConfig, 'id'> = {
    name: 'Camera',
    source_type: 'ip_camera',
    stream_url: 'rtsp://camera/stream',
    auth_required: false,
};

describe('useCreateSource', () => {
    it('shows success toast and requests the source test once', async () => {
        const testSourceSpy = rs.fn();
        server.use(
            http.post('/api/sources', () => HttpResponse.json({ ...body, id: 'new-id' })),
            http.post('/api/sources/{source_id}:test', () => {
                testSourceSpy();

                return HttpResponse.json({ reachable: true, latency_ms: 10, error: null });
            })
        );

        const { result } = renderHook(() => useCreateSource());

        await act(async () => {
            const response = await result.current.mutateAsync({ body });
            expect(response.id).toBe('new-id');
        });

        await waitFor(() => {
            expect(screen.getByText('Source configuration created successfully.')).toBeVisible();
            expect(testSourceSpy).toHaveBeenCalledTimes(1);
        });
    });

    it('shows error toast with details when creating fails', async () => {
        server.use(
            http.post('/api/sources', () => HttpResponse.json({ detail: 'name taken' } as never, { status: 409 }))
        );

        const { result } = renderHook(() => useCreateSource());

        await act(async () => {
            await result.current.mutateAsync({ body }).catch(() => undefined);
        });

        await waitFor(() => {
            expect(screen.getByText('Failed to save source configuration, name taken')).toBeVisible();
        });
        expect(screen.getAllByText(/name taken/)).toHaveLength(1);
    });
});
