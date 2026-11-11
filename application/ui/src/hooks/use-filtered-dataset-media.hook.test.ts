// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { act, waitFor } from '@testing-library/react';
import { getMockedMediaImage } from 'mocks/mock-media';
import { delay, HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../api/utils';
import { server } from '../msw-node-setup';
import { SORT_DIRECTION_PARAM } from './use-dataset-filters-search-params.hook';
import { DATASET_VIEW_ID_PARAM } from './use-dataset-view-id.hook';
import { useFilteredDatasetMedia } from './use-filtered-dataset-media.hook';

const mockMediaResponses = ({ total, nextPageDelayMs = 0 }: { total: number; nextPageDelayMs?: number }) => {
    const requests: URLSearchParams[] = [];

    server.use(
        http.get('/api/projects/{project_id}/dataset/media', async ({ request }) => {
            const searchParams = new URL(request.url).searchParams;
            const offset = Number(searchParams.get('offset') ?? '0');
            requests.push(searchParams);

            if (offset > 0) {
                await delay(nextPageDelayMs);
            }

            return HttpResponse.json({
                items: [getMockedMediaImage({ id: `media-${offset + 1}` })],
                pagination: { offset, count: 1, total, limit: 0 },
            });
        })
    );

    return requests;
};

describe('useFilteredDatasetMedia', () => {
    it('lists the media without requesting the dataset items', async () => {
        const datasetItemsRequest = rs.fn();
        mockMediaResponses({ total: 1 });
        server.use(
            http.get('/api/projects/{project_id}/dataset/items', () => {
                datasetItemsRequest();

                return HttpResponse.json({ items: [], pagination: { offset: 0, count: 0, total: 0, limit: 0 } });
            })
        );

        const { result } = renderHook(() => useFilteredDatasetMedia());

        await waitFor(() => expect(result.current.isPending).toBe(false));

        expect(result.current.items.map(({ id }) => id)).toEqual(['media-1']);
        expect(result.current.totalCount).toBe(1);
        expect(datasetItemsRequest).not.toHaveBeenCalled();
    });

    describe('pagination', () => {
        it('is not fetching a next page during the initial load', async () => {
            mockMediaResponses({ total: 1 });

            const { result } = renderHook(() => useFilteredDatasetMedia());

            // The initial load uses isPending: the gallery would otherwise render a tile-sized loader instead of the
            // full-page overlay.
            expect(result.current.isFetchingNextPage).toBe(false);

            await waitFor(() => expect(result.current.isPending).toBe(false));

            expect(result.current.isFetchingNextPage).toBe(false);
        });

        it('fetches the next page when there is one', async () => {
            const requests = mockMediaResponses({ total: 41, nextPageDelayMs: 100 });

            const { result } = renderHook(() => useFilteredDatasetMedia());

            await waitFor(() => expect(result.current.isPending).toBe(false));

            act(() => result.current.fetchNextPage());

            await waitFor(() => expect(result.current.isFetchingNextPage).toBe(true));
            await waitFor(() => expect(result.current.isFetchingNextPage).toBe(false));

            expect(requests.map((searchParams) => searchParams.get('offset'))).toEqual(['0', '40']);
            expect(result.current.items).toHaveLength(2);
        });

        it('does not request another page when every media is already loaded', async () => {
            const requests = mockMediaResponses({ total: 1 });

            const { result } = renderHook(() => useFilteredDatasetMedia());

            await waitFor(() => expect(result.current.isPending).toBe(false));

            act(() => result.current.fetchNextPage());

            expect(result.current.isFetchingNextPage).toBe(false);
            expect(requests).toHaveLength(1);
        });
    });

    describe('URL filters', () => {
        it('requests the media sorted by upload date, descending by default', async () => {
            const requests = mockMediaResponses({ total: 1 });

            const { result } = renderHook(() => useFilteredDatasetMedia());

            await waitFor(() => expect(result.current.isPending).toBe(false));

            expect(requests[0].get('sort_by')).toBe('upload_date');
            expect(requests[0].get('sort_direction')).toBe('desc');
        });

        it('requests ascending order when the URL sort param is "asc"', async () => {
            const requests = mockMediaResponses({ total: 1 });

            const { result } = renderHook(() => useFilteredDatasetMedia(), {
                route: `/projects/123?${SORT_DIRECTION_PARAM}=asc`,
                path: '/projects/:projectId',
            });

            await waitFor(() => expect(result.current.isPending).toBe(false));

            expect(requests[0].get('sort_direction')).toBe('asc');
        });

        it('omits dataset_view_id when the entire dataset is selected', async () => {
            const requests = mockMediaResponses({ total: 1 });

            const { result } = renderHook(() => useFilteredDatasetMedia());

            await waitFor(() => expect(result.current.isPending).toBe(false));

            expect(requests[0].has('dataset_view_id')).toBe(false);
        });

        it('sends dataset_view_id when a view is selected', async () => {
            const requests = mockMediaResponses({ total: 1 });

            const { result } = renderHook(() => useFilteredDatasetMedia(), {
                route: `/projects/123?${DATASET_VIEW_ID_PARAM}=collection-one`,
                path: '/projects/:projectId',
            });

            await waitFor(() => expect(result.current.isPending).toBe(false));

            expect(requests[0].get('dataset_view_id')).toBe('collection-one');
        });
    });
});
