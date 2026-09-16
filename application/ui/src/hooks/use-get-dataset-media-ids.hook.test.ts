// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { renderHook, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { vi } from 'vitest';

import { http } from '../api/utils';
import { server } from '../msw-node-setup';
import { useGetDatasetMediaIds } from './use-get-dataset-media-ids.hook';

vi.mock('hooks/use-project-identifier.hook', () => ({
    useProjectIdentifier: () => 'project-123',
}));

describe('useGetDatasetMediaIds', () => {
    beforeEach(() => {
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/ids', () => {
                return HttpResponse.json({
                    items: [
                        { id: '1', type: 'image' },
                        { id: '2', type: 'image' },
                    ],
                });
            })
        );
    });

    it('returns a function that fetches all media IDs', async () => {
        const { result } = renderHook(() => useGetDatasetMediaIds());

        let ids: string[] = [];
        await waitFor(async () => {
            ids = await result.current();
        });

        expect(ids).toEqual(['1', '2']);
    });
});
