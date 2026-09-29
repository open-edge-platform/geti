// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { waitFor } from '@testing-library/react';
import { getMockedMediaImage } from 'mocks/mock-media';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { usePrefetchMediaItem } from './use-prefetch-media-item.hook';

const mediaItem = getMockedMediaImage({ id: 'media-2' });

describe('usePrefetchMediaItem', () => {
    const setupAnnotationsHandler = () => {
        const requestedPaths: string[] = [];

        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', ({ request }) => {
                requestedPaths.push(new URL(request.url).pathname);

                return HttpResponse.json({
                    media_id: mediaItem.id,
                    subset: 'training' as const,
                    user_reviewed: true,
                    prediction_model_id: null,
                    annotations: [],
                });
            })
        );

        return requestedPaths;
    };

    it('fetches the annotations of the media item ahead of time', async () => {
        const requestedPaths = setupAnnotationsHandler();

        renderHook(() => usePrefetchMediaItem(mediaItem));

        await waitFor(() => {
            expect(requestedPaths).toEqual([expect.stringContaining(mediaItem.id)]);
        });
    });

    it('does not fetch anything when there is no media item to prefetch', async () => {
        const requestedPaths = setupAnnotationsHandler();

        renderHook(() => usePrefetchMediaItem(undefined));

        await waitFor(() => {
            expect(requestedPaths).toHaveLength(0);
        });
    });
});
