// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { act, waitFor } from '@testing-library/react';
import { getMockedMediaImage, getMockedVideo, getMockedVideoFrame } from 'mocks/mock-media';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { paths } from '../../../../constants/paths';
import { useGetDatasetMediaItems } from '../../../../hooks/use-get-dataset-media-items.hook';
import { server } from '../../../../msw-node-setup';
import { useSelectDatasetItem } from './use-select-dataset-item.hook';

const mockNavigate = vi.fn();

vi.mock('react-router', async (importOriginal) => {
    const actual = await importOriginal<typeof import('react-router')>();
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    };
});

const mockDatasetMediaItems = {
    items: [] as Media[],
    fetchNextPage: vi.fn(),
    hasNextPage: false,
    isFetchingNextPage: false,
    isPending: false,
    totalCount: 0,
};

vi.mock('../../../../hooks/use-get-dataset-media-items.hook', () => ({
    useGetDatasetMediaItems: vi.fn(() => mockDatasetMediaItems),
}));

const MOCKED_PROJECT_ID = '123';

vi.mock('../../../../hooks/use-project-identifier.hook', () => ({
    useProjectIdentifier: vi.fn(() => MOCKED_PROJECT_ID),
}));

const SEARCH = '?annotationStatusFilter=with_annotations';

describe('useSelectDatasetItem', () => {
    beforeEach(() => {
        mockNavigate.mockClear();
        vi.mocked(useGetDatasetMediaItems).mockReturnValue({ ...mockDatasetMediaItems, items: [] });
    });

    describe('onSelectedMediaItemChange', () => {
        it('navigates to dataset index with preserved search when item is null', () => {
            const route = `${paths.project.dataset.index({ projectId: MOCKED_PROJECT_ID })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.index.pattern,
            });

            act(() => {
                result.current.onSelectedMediaItemChange(null);
            });

            expect(mockNavigate).toHaveBeenCalledWith({
                pathname: paths.project.dataset.index({ projectId: MOCKED_PROJECT_ID }),
                search: SEARCH,
            });
        });

        it('navigates to frame 0 with preserved search for a video item', () => {
            const video = getMockedVideo({ id: 'video-42' });
            const route = `${paths.project.dataset.index({ projectId: MOCKED_PROJECT_ID })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.index.pattern,
            });

            act(() => {
                result.current.onSelectedMediaItemChange(video);
            });

            expect(mockNavigate).toHaveBeenCalledWith({
                pathname: paths.project.dataset.item.frame({
                    datasetItemId: video.id,
                    frameNumber: '0',
                    projectId: MOCKED_PROJECT_ID,
                }),
                search: SEARCH,
            });
        });

        it('navigates to the correct frame number with preserved search for a video frame item', () => {
            const videoFrame = getMockedVideoFrame({ id: 'vf-7', frame_number: 42 });
            const route = `${paths.project.dataset.index({ projectId: MOCKED_PROJECT_ID })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.index.pattern,
            });

            act(() => {
                result.current.onSelectedMediaItemChange(videoFrame);
            });

            expect(mockNavigate).toHaveBeenCalledWith({
                pathname: paths.project.dataset.item.frame({
                    datasetItemId: videoFrame.id,
                    frameNumber: videoFrame.frame_number.toString(),
                    projectId: MOCKED_PROJECT_ID,
                }),
                search: SEARCH,
            });
        });

        it('navigates to item index with preserved search for an image item', () => {
            const image = getMockedMediaImage({ id: 'img-99' });
            const route = `${paths.project.dataset.index({ projectId: MOCKED_PROJECT_ID })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.index.pattern,
            });

            act(() => {
                result.current.onSelectedMediaItemChange(image);
            });

            expect(mockNavigate).toHaveBeenCalledWith({
                pathname: paths.project.dataset.item.index({
                    datasetItemId: image.id,
                    projectId: MOCKED_PROJECT_ID,
                }),
                search: SEARCH,
            });
        });

        it('preserves an empty search string when there are no query params', () => {
            const image = getMockedMediaImage({ id: 'img-1' });
            const route = paths.project.dataset.index({ projectId: MOCKED_PROJECT_ID });

            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.index.pattern,
            });

            act(() => {
                result.current.onSelectedMediaItemChange(image);
            });

            expect(mockNavigate).toHaveBeenCalledWith({
                pathname: paths.project.dataset.item.index({
                    datasetItemId: image.id,
                    projectId: MOCKED_PROJECT_ID,
                }),
                search: '',
            });
        });
    });

    describe('selectedMediaItem', () => {
        it('returns the matching item when datasetItemId param matches an item in the list', () => {
            const image = getMockedMediaImage({ id: 'img-selected' });
            vi.mocked(useGetDatasetMediaItems).mockReturnValue({ ...mockDatasetMediaItems, items: [image] });

            const route = `${paths.project.dataset.item.index({ projectId: MOCKED_PROJECT_ID, datasetItemId: image.id })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.item.index.pattern,
            });

            expect(result.current.selectedMediaItem).toEqual(image);
        });

        it('returns null when datasetItemId does not match any item', () => {
            const image = getMockedMediaImage({ id: 'img-other' });
            vi.mocked(useGetDatasetMediaItems).mockReturnValue({ ...mockDatasetMediaItems, items: [image] });
            server.use(
                http.get('/api/projects/{project_id}/dataset/media/{media_id}', () => {
                    return new HttpResponse(null, { status: 404 });
                })
            );

            const route = `${paths.project.dataset.item.index({ projectId: MOCKED_PROJECT_ID, datasetItemId: `${image.id}-23` })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.item.index.pattern,
            });

            expect(result.current.selectedMediaItem).toBeNull();
        });

        it('is resolving while the direct fetch for an off-list item is in flight', async () => {
            const image = getMockedMediaImage({ id: 'img-off-page' });
            vi.mocked(useGetDatasetMediaItems).mockReturnValue({ ...mockDatasetMediaItems, items: [] });
            server.use(
                http.get('/api/projects/{project_id}/dataset/media/{media_id}', async () => {
                    return HttpResponse.json(image);
                })
            );

            const route = `${paths.project.dataset.item.index({ projectId: MOCKED_PROJECT_ID, datasetItemId: image.id })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.item.index.pattern,
            });

            expect(result.current.isResolving).toBe(true);
            expect(result.current.fetchErrorMessage).toBeNull();

            await waitFor(() => expect(result.current.selectedMediaItem).toEqual(image));
        });

        it('returns the fetched item when it is not in the loaded list but the direct fetch resolves it', async () => {
            const image = getMockedMediaImage({ id: 'img-off-page' });
            vi.mocked(useGetDatasetMediaItems).mockReturnValue({ ...mockDatasetMediaItems, items: [] });
            server.use(
                http.get('/api/projects/{project_id}/dataset/media/{media_id}', () => {
                    return HttpResponse.json(image);
                })
            );

            const route = `${paths.project.dataset.item.index({ projectId: MOCKED_PROJECT_ID, datasetItemId: image.id })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.item.index.pattern,
            });

            await waitFor(() => expect(result.current.selectedMediaItem).toEqual(image));
            expect(result.current.isResolving).toBe(false);
            expect(result.current.fetchErrorMessage).toBeNull();
        });

        it('surfaces the server error message when the direct fetch errors', async () => {
            vi.mocked(useGetDatasetMediaItems).mockReturnValue({ ...mockDatasetMediaItems, items: [] });
            server.use(
                http.get('/api/projects/{project_id}/dataset/media/{media_id}', () => {
                    // @ts-expect-error MSW's typed response doesn't document a JSON body for 404s,
                    // but the server does return one at runtime.
                    return HttpResponse.json({ detail: 'Media or project not found' }, { status: 404 });
                })
            );

            const route = `${paths.project.dataset.item.index({ projectId: MOCKED_PROJECT_ID, datasetItemId: 'deleted-item' })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.item.index.pattern,
            });

            await waitFor(() => expect(result.current.fetchErrorMessage).toBe('Media or project not found'));
            expect(result.current.selectedMediaItem).toBeNull();
            expect(result.current.isResolving).toBe(false);
        });

        it('returns null when there are no items', () => {
            vi.mocked(useGetDatasetMediaItems).mockReturnValue({ ...mockDatasetMediaItems, items: [] });
            server.use(
                http.get('/api/projects/{project_id}/dataset/media/{media_id}', () => {
                    return new HttpResponse(null, { status: 404 });
                })
            );

            const route = `${paths.project.dataset.item.index({ projectId: MOCKED_PROJECT_ID, datasetItemId: `img-selected` })}${SEARCH}`;
            const { result } = renderHook(() => useSelectDatasetItem(), {
                route,
                path: paths.project.dataset.item.index.pattern,
            });

            expect(result.current.selectedMediaItem).toBeNull();
        });
    });
});
