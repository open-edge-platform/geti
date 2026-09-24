// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { act, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../../api/utils';
import { server } from '../../../../../msw-node-setup';
import { useBulkAssignLabel } from './use-bulk-assign-label';

describe('useBulkAssignLabel', () => {
    it('keeps the number of concurrent requests bounded for a large selection', async () => {
        const mediaIds = Array.from({ length: 100 }, (_, index) => `media-${index}`);

        let inFlight = 0;
        let maxInFlight = 0;
        let totalRequests = 0;

        server.use(
            http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async () => {
                inFlight += 1;
                totalRequests += 1;
                maxInFlight = Math.max(maxInFlight, inFlight);

                await new Promise((resolve) => setTimeout(resolve, 0));

                inFlight -= 1;

                return HttpResponse.json({ annotations: [], user_reviewed: false, subset: 'unassigned' });
            })
        );

        const { result } = renderHook(() => useBulkAssignLabel());

        await act(async () => {
            await result.current.mutate(mediaIds, ['label-1']);
        });

        await waitFor(() => {
            expect(totalRequests).toBe(mediaIds.length);
        });

        expect(maxInFlight).toBe(10);
    });
});
