// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useMemo, useRef } from 'react';

import type { AnnotationDTO, Media } from '@/api/types';
import { useQuery } from '@tanstack/react-query';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { useDatasetMediaWithReviewStatus } from 'hooks/use-dataset-media-with-review-status.hook';
import { useFetchNextUnannotatedMediaItem } from 'hooks/use-get-dataset-items.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { range } from 'lodash-es';
import { useLocalStorage } from 'usehooks-ts';

import type { AnnotatorMode } from '../../../shared/annotator/annotator-mode';
import { isVideoFrame } from '../../../shared/media-item-utils';
import { loadImageQueryOptions } from '../../annotator/hooks/use-load-image-query.hook';
import { useVideoPlayerContext } from '../../annotator/video-player/video-player-provider.component';
import { annotationsQueryOptions } from './api/use-annotations-query';

export const getInitialAnnotations = (isUserReviewed: boolean, annotationsDTO: AnnotationDTO[]): AnnotationDTO[] => {
    return isUserReviewed ? annotationsDTO : [];
};

export const getNextMediaItem = (currentMediaItem: Media, allMediaItems: Media[], step: number): Media | undefined => {
    if (isVideoFrame(currentMediaItem)) {
        const videoFrames = range(0, currentMediaItem.frame_count, step);
        const currentIndex = videoFrames.findIndex((frame) => frame === currentMediaItem.frame_number);

        if (currentIndex >= 0 && currentIndex < videoFrames.length - 1) {
            return {
                ...currentMediaItem,
                frame_number: videoFrames[currentIndex + 1],
            };
        } else {
            const nextFrame = videoFrames.find((frame) => frame > currentMediaItem.frame_number);

            if (nextFrame !== undefined) {
                return {
                    ...currentMediaItem,
                    frame_number: nextFrame ?? 0,
                };
            }
        }
    }

    const currentIndex = allMediaItems.findIndex(({ id }) => id === currentMediaItem.id);

    if (currentIndex < 0) {
        return allMediaItems[0];
    }

    if (currentIndex >= allMediaItems.length - 1) {
        return undefined;
    }

    return allMediaItems[currentIndex + 1];
};

const useNextUnannotatedMediaItem = (currentMediaItem: Media, allMediaItems: Media[]) => {
    const { annotationStatus } = useDatasetFiltersSearchParams();
    const { fetchNextPage, hasNextPage, isFetchingNextPage } = useDatasetMediaWithReviewStatus();
    const { data, isPending, refetch } = useFetchNextUnannotatedMediaItem();
    const items = data?.items ?? [];

    // Only relevant when the gallery can actually contain unannotated media.
    // When the active filter is restricted to "with_annotations", no unannotated
    // item can ever appear in a list, so searching for one would just
    // paginate through the entire filtered dataset looking for something that
    // can never be found.
    const canNavigateToUnannotated = annotationStatus !== 'with_annotations';

    const nextUnannotatedDatasetMediaItem = canNavigateToUnannotated
        ? items.find((item) => item.id !== currentMediaItem.id)
        : undefined;
    const nextUnannotatedMediaItem = allMediaItems.find((item) => item.id === nextUnannotatedDatasetMediaItem?.id);
    const isInsideFetchedMediaItems = nextUnannotatedMediaItem !== undefined;

    useEffect(() => {
        // When we navigate to the next media item, we need to refresh the list of the next unannotated media items
        // because the current media item has changed, and it may affect the next unannotated media item.
        refetch();
    }, [currentMediaItem.id, refetch]);

    useEffect(() => {
        // Nothing to do if we can't/shouldn't look for an unannotated item, the
        // candidate is already loaded, or there's no known candidate to look for
        // (fetching further pages wouldn't help find something that doesn't exist).
        if (
            !canNavigateToUnannotated ||
            isPending ||
            isInsideFetchedMediaItems ||
            nextUnannotatedDatasetMediaItem === undefined ||
            !hasNextPage ||
            isFetchingNextPage
        ) {
            return;
        }

        fetchNextPage();
    }, [
        canNavigateToUnannotated,
        isPending,
        isInsideFetchedMediaItems,
        nextUnannotatedDatasetMediaItem,
        hasNextPage,
        isFetchingNextPage,
        fetchNextPage,
    ]);

    if (isPending || !canNavigateToUnannotated) {
        return undefined;
    }

    return nextUnannotatedMediaItem;
};

export const useNextMediaItem = (currentMediaItem: Media, allMediaItems: Media[]) => {
    const context = useVideoPlayerContext();
    const step = context?.step ?? 1;
    const nextUnannotatedMediaItem = useNextUnannotatedMediaItem(currentMediaItem, allMediaItems);

    return useMemo(() => {
        if (isVideoFrame(currentMediaItem) || nextUnannotatedMediaItem === undefined) {
            return getNextMediaItem(currentMediaItem, allMediaItems, step);
        }

        return nextUnannotatedMediaItem;
    }, [allMediaItems, currentMediaItem, step, nextUnannotatedMediaItem]);
};

// When the user navigates to next media, image data and annotations will be already in React Query cache,
// so the UI will feel smoother whenever the user switches image unless the user changes to a random or item.
// We could also consider those cases but I feel like it's overkill.
// Let's see how this improvement performs and then we can iterate on it.
//
// We trigger next-item data prefetch through disabled/conditional query hooks,
// so data is resolved from cache when available and fetched when needed.
export const useNextMediaPrefetch = (currentMediaItem: Media, allMediaItems: Media[]) => {
    const projectId = useProjectIdentifier();
    const nextMediaItem = useNextMediaItem(currentMediaItem, allMediaItems);

    const nextImageQuery = useQuery({
        ...loadImageQueryOptions(projectId, nextMediaItem ?? currentMediaItem),
        enabled: nextMediaItem !== undefined,
    });

    useQuery({
        ...annotationsQueryOptions(projectId, nextMediaItem ?? currentMediaItem),
        enabled: nextMediaItem !== undefined,
    });

    return {
        nextMediaItem,
        nextImage: nextImageQuery.data,
        isNextImageReady: nextImageQuery.isSuccess,
    };
};

export const useAnnotatorMode = () => {
    const projectId = useProjectIdentifier();

    const [mode, setMode] = useLocalStorage<AnnotatorMode>(`${projectId}-annotator-mode`, 'annotation');

    return [mode, setMode] as const;
};

export const usePlayPauseVideoBySystem = (isLoadingRangePredictions: boolean) => {
    const isPausedBySystem = useRef<boolean>(false);
    const context = useVideoPlayerContext();

    const playRef = useRef(context?.videoControls.play);
    const pauseRef = useRef(context?.videoControls.pause);

    useEffect(() => {
        playRef.current = context?.videoControls.play;
    }, [context?.videoControls.play]);

    useEffect(() => {
        pauseRef.current = context?.videoControls.pause;
    }, [context?.videoControls.pause]);

    useEffect(() => {
        if (isLoadingRangePredictions && context?.videoControls.isPlaying) {
            isPausedBySystem.current = true;
            pauseRef.current?.();
        } else if (!isLoadingRangePredictions && isPausedBySystem.current) {
            isPausedBySystem.current = false;
            playRef.current?.();
        }
    }, [isLoadingRangePredictions, context?.videoControls.isPlaying]);
};
