// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationDTO } from '@/api/types';
import { act } from '@testing-library/react';
import { useDatasetMediaWithReviewStatus } from 'hooks/use-dataset-media-with-review-status.hook';
import { useFetchNextUnannotatedMediaItem } from 'hooks/use-get-dataset-items.hook';
import { getMockedDatasetItem } from 'mocks/mock-dataset-item';
import { getMockedMediaImage, getMockedVideoFrame, getMultipleMockedMediaImage } from 'mocks/mock-media';
import { renderHook } from 'test-utils/render';

import { useVideoPlayerContext } from '../../annotator/video-player/video-player-provider.component';
import { getInitialAnnotations, getNextMediaItem, useNextMediaItem, usePlayPauseVideoBySystem } from './utils';

vi.mock('../../annotator/video-player/video-player-provider.component', () => ({
    useVideoPlayerContext: vi.fn(),
}));

vi.mock('hooks/use-dataset-media-with-review-status.hook', () => ({
    useDatasetMediaWithReviewStatus: vi.fn(),
}));

vi.mock('hooks/use-get-dataset-items.hook', () => ({
    useFetchNextUnannotatedMediaItem: vi.fn(),
}));

const mockUseVideoPlayerContext = vi.mocked(useVideoPlayerContext);
const mockUseDatasetMediaWithReviewStatus = vi.mocked(useDatasetMediaWithReviewStatus);
const mockUseFetchNextUnannotatedMediaItem = vi.mocked(useFetchNextUnannotatedMediaItem);

const createVideoPlayerContext = (isPlaying: boolean) => {
    const play = vi.fn().mockResolvedValue(undefined);
    const pause = vi.fn();
    return {
        videoControls: { isPlaying, play, pause },
    };
};

describe('getInitialAnnotations', () => {
    const mockAnnotations: AnnotationDTO[] = [
        {
            shape: { type: 'rectangle', x: 0, y: 0, width: 100, height: 100 },
            labels: [{ id: '1' }],
        },
        {
            shape: {
                type: 'polygon',
                points: [
                    { x: 0, y: 0 },
                    { x: 100, y: 100 },
                ],
            },
            labels: [{ id: '2' }],
        },
        {
            shape: { type: 'full_image' },
            labels: [{ id: '3' }],
        },
    ];

    it('returns annotations when user has reviewed', () => {
        const result = getInitialAnnotations(true, mockAnnotations);
        expect(result).toEqual(mockAnnotations);
    });

    it('returns empty array when user has not reviewed', () => {
        const result = getInitialAnnotations(false, mockAnnotations);
        expect(result).toEqual([]);
    });
});

describe('getNextMediaItem', () => {
    describe('image media items', () => {
        it('returns the next image in the list', () => {
            const items = getMultipleMockedMediaImage(3);
            const result = getNextMediaItem(items[0], items, 1);
            expect(result).toEqual(items[1]);
        });

        it('returns undefined when current item is the last one', () => {
            const items = getMultipleMockedMediaImage(3);
            const result = getNextMediaItem(items[2], items, 1);
            expect(result).toBeUndefined();
        });

        it('returns the first item when current item is not found in the list', () => {
            const items = getMultipleMockedMediaImage(3);
            const unknownItem = getMockedMediaImage({ id: 'unknown' });
            const result = getNextMediaItem(unknownItem, items, 1);
            expect(result).toEqual(items[0]);
        });
    });

    describe('video frame media items', () => {
        it('returns the next video frame based on step', () => {
            const frame = getMockedVideoFrame({ frame_number: 0, frame_count: 10 });
            const result = getNextMediaItem(frame, [], 1);
            expect(result).toEqual({ ...frame, frame_number: 1 });
        });

        it('advances by the given step size', () => {
            const frame = getMockedVideoFrame({ frame_number: 0, frame_count: 10 });
            const result = getNextMediaItem(frame, [], 3);
            expect(result).toEqual({ ...frame, frame_number: 3 });
        });

        it('advances to the next media item when already at the last video frame', () => {
            const frame = getMockedVideoFrame({ id: 'video-1', frame_number: 9, frame_count: 10 });
            const nextImage = getMockedMediaImage({ id: 'image-1' });
            const result = getNextMediaItem(frame, [frame, nextImage], 1);
            expect(result).toEqual(nextImage);
        });

        it('returns undefined when it is the last media item and already at the last frame', () => {
            const frame = getMockedVideoFrame({ id: 'video-1', frame_number: 9, frame_count: 10 });
            const result = getNextMediaItem(frame, [frame], 1);
            expect(result).toBeUndefined();
        });

        it('advances to the next media item when at the last frame', () => {
            const frame = getMockedVideoFrame({ id: 'video-1', frame_number: 9, frame_count: 10 });
            const nextImage = getMockedMediaImage({ id: 'image-1' });
            const result = getNextMediaItem(frame, [frame, nextImage], 3);
            expect(result).toEqual(nextImage);
        });

        it('handles a frame_number that is not aligned with the step', () => {
            const frame = getMockedVideoFrame({ id: 'video-1', frame_number: 5, frame_count: 10 });
            const result = getNextMediaItem(frame, [frame], 3);
            expect(result).toEqual({ ...frame, frame_number: 6 });
        });
    });
});

describe('useNextMediaItem', () => {
    const mockFetchNextPage = vi.fn();

    beforeEach(() => {
        mockUseVideoPlayerContext.mockReturnValue(null);
        // @ts-expect-error We only care about mocking part of the context for this test.
        mockUseDatasetMediaWithReviewStatus.mockReturnValue({ fetchNextPage: mockFetchNextPage });
        // @ts-expect-error We only care about mocking data and isPending for this test.
        mockUseFetchNextUnannotatedMediaItem.mockReturnValue({ data: { items: [] }, isPending: false });
        vi.clearAllMocks();
    });

    it('prefers the next unannotated media item over the positional next item', () => {
        const items = getMultipleMockedMediaImage(3);
        mockUseFetchNextUnannotatedMediaItem.mockReturnValue({
            // @ts-expect-error We only care about mocking data and isPending for this test.
            data: { items: [getMockedDatasetItem({ id: items[2].id })] },
            isPending: false,
        });

        const { result } = renderHook(() => useNextMediaItem(items[0], items));

        expect(result.current).toEqual(items[2]);
    });

    it('falls back to the positional next item when every media item is annotated', () => {
        const items = getMultipleMockedMediaImage(3);

        const { result } = renderHook(() => useNextMediaItem(items[0], items));

        expect(result.current).toEqual(items[1]);
    });

    it('ignores annotation status and advances by frame when the current item is a video frame', () => {
        const frame = getMockedVideoFrame({ id: 'video-1', frame_number: 0, frame_count: 10 });
        const nextImage = getMockedMediaImage({ id: 'image-1' });
        mockUseFetchNextUnannotatedMediaItem.mockReturnValue({
            // @ts-expect-error We only care about mocking data and isPending for this test.
            data: { items: [getMockedDatasetItem({ id: nextImage.id })] },
            isPending: false,
        });

        const { result } = renderHook(() => useNextMediaItem(frame, [frame, nextImage]));

        expect(result.current).toEqual({ ...frame, frame_number: 1 });
    });

    it('advances video frames using the step size from the video player context', async () => {
        // @ts-expect-error We only care about mocking only step for this test.
        mockUseVideoPlayerContext.mockReturnValue({ step: 60 });
        const frame = getMockedVideoFrame({ id: 'video-1', frame_number: 0, frame_count: 70 });

        const { result } = renderHook(() => useNextMediaItem(frame, [frame]));

        expect(result.current).toEqual({ ...frame, frame_number: 60 });
    });

    it('excludes the current item from the unannotated candidates', () => {
        const items = getMultipleMockedMediaImage(2);
        mockUseFetchNextUnannotatedMediaItem.mockReturnValue({
            // @ts-expect-error We only care about mocking data and isPending for this test.
            data: { items: [getMockedDatasetItem({ id: items[0].id })] },
            isPending: false,
        });

        const { result } = renderHook(() => useNextMediaItem(items[0], items));

        expect(result.current).toEqual(items[1]);
    });

    it('fetches the next page when the next unannotated item is not among the already-fetched items', () => {
        const alreadyFetchedItems = getMultipleMockedMediaImage(2);
        const nextUnannotatedItem = getMockedDatasetItem({ id: 'not-loaded-item' });
        const nextUnannotatedMediaImage = getMockedMediaImage({ id: nextUnannotatedItem.id });
        mockUseFetchNextUnannotatedMediaItem.mockReturnValue({
            // @ts-expect-error We only care about mocking data and isPending for this test.
            data: { items: [nextUnannotatedItem] },
            isPending: false,
        });

        const { result, rerender } = renderHook(() => useNextMediaItem(alreadyFetchedItems[0], alreadyFetchedItems));

        expect(mockFetchNextPage).toHaveBeenCalledTimes(1);

        alreadyFetchedItems.push(nextUnannotatedMediaImage);

        rerender();

        expect(result.current).toEqual(nextUnannotatedMediaImage);
    });

    it('does not fetch the next page when the next unannotated item is already among the fetched items', () => {
        const alreadyFetchedItems = getMultipleMockedMediaImage(2);
        mockUseFetchNextUnannotatedMediaItem.mockReturnValue({
            // @ts-expect-error We only care about mocking data and isPending for this test.
            data: { items: [getMockedDatasetItem({ id: alreadyFetchedItems[1].id })] },
            isPending: false,
        });

        renderHook(() => useNextMediaItem(alreadyFetchedItems[0], alreadyFetchedItems));

        expect(mockFetchNextPage).not.toHaveBeenCalled();
    });
});

describe('usePlayPauseVideoBySystem', () => {
    beforeEach(() => {
        mockUseVideoPlayerContext.mockReturnValue(null);
    });

    it('does not call play or pause when not loading and video is not playing', () => {
        const context = createVideoPlayerContext(false);
        // @ts-expect-error We only care about mocking part of the context for this test.
        mockUseVideoPlayerContext.mockReturnValue(context);

        renderHook(() => usePlayPauseVideoBySystem(false));

        expect(context.videoControls.play).not.toHaveBeenCalled();
        expect(context.videoControls.pause).not.toHaveBeenCalled();
    });

    it('calls pause when range predictions are loading and video is playing', () => {
        const context = createVideoPlayerContext(true);
        // @ts-expect-error We only care about mocking part of the context for this test.
        mockUseVideoPlayerContext.mockReturnValue(context);

        renderHook(() => usePlayPauseVideoBySystem(true));

        expect(context.videoControls.pause).toHaveBeenCalledTimes(1);
        expect(context.videoControls.play).not.toHaveBeenCalled();
    });

    it('calls play when range predictions stop loading after system paused the video', () => {
        const context = createVideoPlayerContext(true);
        // @ts-expect-error We only care about mocking part of the context for this test.
        mockUseVideoPlayerContext.mockReturnValue(context);

        let isLoading = true;
        const { rerender } = renderHook(() => usePlayPauseVideoBySystem(isLoading));

        expect(context.videoControls.pause).toHaveBeenCalledTimes(1);

        act(() => {
            isLoading = false;
            rerender();
        });

        expect(context.videoControls.play).toHaveBeenCalledTimes(1);
    });

    it('does not call play when range predictions stop loading but video was paused by user', () => {
        const context = createVideoPlayerContext(false);
        // @ts-expect-error We only care about mocking part of the context for this test.
        mockUseVideoPlayerContext.mockReturnValue(context);

        let isLoading = true;
        const { rerender } = renderHook(() => usePlayPauseVideoBySystem(isLoading));

        expect(context.videoControls.pause).not.toHaveBeenCalled();

        act(() => {
            isLoading = false;
            rerender();
        });

        expect(context.videoControls.play).not.toHaveBeenCalled();
    });

    it('does not call pause when video is not playing and range predictions are loading', () => {
        const context = createVideoPlayerContext(false);
        // @ts-expect-error We only care about mocking part of the context for this test.
        mockUseVideoPlayerContext.mockReturnValue(context);

        renderHook(() => usePlayPauseVideoBySystem(true));

        expect(context.videoControls.pause).not.toHaveBeenCalled();
    });
});
