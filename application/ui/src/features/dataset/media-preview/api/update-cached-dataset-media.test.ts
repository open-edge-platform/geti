// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MediaDTO, MediaWithPagination } from '@/api/types';
import { InfiniteData, QueryClient } from '@tanstack/react-query';
import { getMockedMediaImage, getMockedVideo } from 'mocks/mock-media';
import { delay, HttpResponse } from 'msw';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { markCachedMediaAsAnnotated, refreshCachedMedia } from './update-cached-dataset-media';

const PROJECT_ID = 'project-1';

const MEDIA_QUERY_KEY = [
    'get',
    '/api/projects/{project_id}/dataset/media',
    { params: { path: { project_id: PROJECT_ID }, query: { offset: 0, limit: 40 } } },
] as const;

const createQueryClientWithPages = (pages: MediaDTO[][]) => {
    const queryClient = new QueryClient();

    queryClient.setQueryData<InfiniteData<MediaWithPagination>>(MEDIA_QUERY_KEY, {
        pages: pages.map((items, index) => ({
            items,
            pagination: { offset: index, limit: 1, count: items.length, total: pages.flat().length },
        })),
        pageParams: pages.map((_, index) => index),
    });

    return queryClient;
};

const getCachedItems = (queryClient: QueryClient) =>
    queryClient.getQueryData<InfiniteData<MediaWithPagination>>(MEDIA_QUERY_KEY)?.pages.map(({ items }) => items);

describe('markCachedMediaAsAnnotated', () => {
    it('marks only the matching media as annotated, on any cached page', () => {
        const target = getMockedMediaImage({ id: 'image-1' });
        const other = getMockedMediaImage({ id: 'image-2' });
        const queryClient = createQueryClientWithPages([[other], [target]]);

        markCachedMediaAsAnnotated(queryClient, target.id);

        expect(getCachedItems(queryClient)).toEqual([
            [other],
            [{ ...target, annotation_status: { has_annotations: true } }],
        ]);
    });

    it('does not modify videos', () => {
        const video = getMockedVideo({
            id: 'video-1',
            annotation_status: { has_annotations: false, annotated_video_frames: 0 },
        });
        const queryClient = createQueryClientWithPages([[video]]);

        markCachedMediaAsAnnotated(queryClient, video.id);

        expect(getCachedItems(queryClient)).toEqual([[video]]);
    });
});

describe('refreshCachedMedia', () => {
    it('replaces the cached media with the one returned by the server', async () => {
        const image = getMockedMediaImage({ id: 'image-1' });
        const video = getMockedVideo({
            id: 'video-1',
            annotation_status: { has_annotations: true, annotated_video_frames: 3 },
        });
        const refreshedVideo = { ...video, annotation_status: { has_annotations: true, annotated_video_frames: 4 } };
        const queryClient = createQueryClientWithPages([[image], [video]]);

        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}', () => HttpResponse.json(refreshedVideo))
        );

        await refreshCachedMedia(queryClient, PROJECT_ID, video.id);

        expect(getCachedItems(queryClient)).toEqual([[image], [refreshedVideo]]);
    });

    it('ignores a response that arrives after the response of a newer refresh of the same media', async () => {
        const video = getMockedVideo({
            id: 'video-1',
            annotation_status: { has_annotations: false, annotated_video_frames: 0 },
        });
        const withAnnotatedFrames = (count: number) => ({
            ...video,
            annotation_status: { has_annotations: true, annotated_video_frames: count },
        });
        const queryClient = createQueryClientWithPages([[video]]);
        let requestCount = 0;

        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}', async () => {
                requestCount += 1;

                // The first (older) request is answered last
                if (requestCount === 1) {
                    await delay(100);

                    return HttpResponse.json(withAnnotatedFrames(1));
                }

                return HttpResponse.json(withAnnotatedFrames(2));
            })
        );

        await Promise.all([
            refreshCachedMedia(queryClient, PROJECT_ID, video.id),
            refreshCachedMedia(queryClient, PROJECT_ID, video.id),
        ]);

        expect(getCachedItems(queryClient)).toEqual([[withAnnotatedFrames(2)]]);
    });

    it('keeps the cache unchanged when the media cannot be fetched', async () => {
        const video = getMockedVideo({ id: 'video-1' });
        const queryClient = createQueryClientWithPages([[video]]);

        server.use(
            http.get(
                '/api/projects/{project_id}/dataset/media/{media_id}',
                () => new HttpResponse(null, { status: 404 })
            )
        );

        await refreshCachedMedia(queryClient, PROJECT_ID, video.id);

        expect(getCachedItems(queryClient)).toEqual([[video]]);
    });
});
