// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteData, QueryKey, useInfiniteQuery, UseInfiniteQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { MediaItemResponse } from '../../../../core/media/media.interface';
import { MediaService } from '../../../../core/media/services/media-service.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { NextPageURL } from '../../../../core/shared/infinite-query.interface';
import { usePrevious } from '../../../../hooks/use-previous/use-previous.hook';
import { useTask } from '../../../annotator/providers/task-provider/task-provider.component';

// We don't want to refetch the active set when the user switches between tasks or dataset
// (i.e. change the datasetIdentifier or selectedTask?.id), therefore we set the stale time
// to Infinity.
// However we do want to refetch when the user opens the annotator, because they may have
// uploaded new media so when this hook is unmounted we reset the stale data.
const useStaleTime = () => {
    const wasUnMounted = usePrevious(null);

    return wasUnMounted === undefined ? undefined : Infinity;
};

export const useActiveMediaQuery = (
    mediaService: MediaService,
    datasetIdentifier: DatasetIdentifier,
    mediaItemsLoadSize = 50
): UseInfiniteQueryResult<InfiniteData<MediaItemResponse>> => {
    const { selectedTask } = useTask();
    const activeQueryKey = QUERY_KEYS.ACTIVE_MEDIA_ITEMS(datasetIdentifier, selectedTask);
    const staleTime = useStaleTime();

    return useInfiniteQuery<MediaItemResponse, AxiosError, InfiniteData<MediaItemResponse>, QueryKey, NextPageURL>({
        queryKey: activeQueryKey,
        queryFn: async ({ pageParam: nextPage = null }) => {
            const { media } = await mediaService.getActiveMedia(
                datasetIdentifier,
                mediaItemsLoadSize,
                selectedTask?.id
            );

            return { media, nextPage, mediaCount: undefined };
        },
        getNextPageParam: (_, pages) => {
            if (pages.length === 1) {
                return 'true';
            }

            // Collect all used media identifiers from previous pages
            const identifiers = new Set();

            for (let idx = 0; idx < pages.length - 1; idx++) {
                pages[idx].media.forEach(({ identifier }) => {
                    identifiers.add(JSON.stringify(identifier));
                });
            }

            // There is a next page if the current page contains unused media identifiers
            const lastPage = pages[pages.length - 1];

            const hasUnusedMediaIdentifiers = lastPage.media.some(({ identifier }) => {
                return !identifiers.has(JSON.stringify(identifier));
            });

            return hasUnusedMediaIdentifiers ? 'true' : undefined;
        },
        getPreviousPageParam: () => undefined,
        // Remove any duplicated media items since active set is not deterministic?
        select: (data) => {
            const identifiers = new Set();

            const pages = data.pages.map((page) => {
                const media = page.media.filter(({ identifier }) => {
                    return !identifiers.has(JSON.stringify(identifier));
                });

                media.forEach(({ identifier }) => {
                    identifiers.add(JSON.stringify(identifier));
                });

                return { ...page, media };
            });

            return { ...data, pages };
        },
        initialPageParam: undefined,
        staleTime,
    });
};
