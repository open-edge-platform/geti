// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MediaDTO, MediaWithPagination } from '@/api/types';
import { InfiniteData, QueryClient } from '@tanstack/react-query';
import {
    buildDatasetMediaQueryFilters,
    type UseGetDatasetMediaItemsOptions,
} from 'hooks/use-get-dataset-media-items.hook';
import { getMockedMediaImage, getMockedVideo } from 'mocks/mock-media';
import { HttpResponse } from 'msw';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { getQueryKey } from '../../../../query-client/query-client';
import {
    invalidateMediaFilteredByAnnotations,
    markCachedMediaAsAnnotated,
    refreshCachedMedia,
} from './update-cached-dataset-media';

const PROJECT_ID = 'project-1';

const getMediaQueryKey = (options?: UseGetDatasetMediaItemsOptions) =>
    getQueryKey([
        'get',
        '/api/projects/{project_id}/dataset/media',
        {
            params: {
                path: { project_id: PROJECT_ID },
                query: { offset: 0, limit: 40, ...buildDatasetMediaQueryFilters(options) },
            },
        },
    ]);

const MEDIA_QUERY_KEY = getMediaQueryKey();

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

describe('invalidateMediaFilteredByAnnotations', () => {
    it.each<[UseGetDatasetMediaItemsOptions, boolean]>([
        [{ annotationStatus: 'missing_annotations' }, true],
        [{ labelIds: ['label-1'] }, true],
        [{ subsets: ['training'] }, true],
        [{}, false],
        [{ labelIds: [], subsets: [] }, false],
        [{ datasetViewId: 'view-1', startDate: '2026-01-01', sortDirection: 'asc' }, false],
    ])('with options %o, invalidates the listing: %s', async (options, isInvalidated) => {
        const queryKey = getMediaQueryKey(options);
        const queryClient = new QueryClient();
        queryClient.setQueryData<InfiniteData<MediaWithPagination>>(queryKey, { pages: [], pageParams: [] });

        await invalidateMediaFilteredByAnnotations(queryClient, PROJECT_ID);

        expect(queryClient.getQueryState(queryKey)?.isInvalidated).toBe(isInvalidated);
    });
});

describe('markCachedMediaAsAnnotated', () => {
    it('does not patch the listings filtered by annotations, which are refetched instead', () => {
        const image = getMockedMediaImage({ id: 'image-1', annotation_status: { has_annotations: false } });
        const filteredQueryKey = getMediaQueryKey({ annotationStatus: 'missing_annotations' });
        const queryClient = createQueryClientWithPages([[image]]);
        queryClient.setQueryData<InfiniteData<MediaWithPagination>>(filteredQueryKey, {
            pages: [{ items: [image], pagination: { offset: 0, limit: 40, count: 1, total: 1 } }],
            pageParams: [0],
        });

        markCachedMediaAsAnnotated(queryClient, PROJECT_ID, image.id);

        expect(getCachedItems(queryClient)).toEqual([[{ ...image, annotation_status: { has_annotations: true } }]]);
        expect(queryClient.getQueryData<InfiniteData<MediaWithPagination>>(filteredQueryKey)?.pages[0].items).toEqual([
            image,
        ]);
    });

    it('marks only the matching media as annotated, on any cached page', () => {
        const target = getMockedMediaImage({ id: 'image-1' });
        const other = getMockedMediaImage({ id: 'image-2' });
        const queryClient = createQueryClientWithPages([[other], [target]]);

        markCachedMediaAsAnnotated(queryClient, PROJECT_ID, target.id);

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

        markCachedMediaAsAnnotated(queryClient, PROJECT_ID, video.id);

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
