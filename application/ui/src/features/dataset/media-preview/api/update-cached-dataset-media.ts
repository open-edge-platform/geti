// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fetchClient } from '@/api';
import type { MediaDTO, MediaWithPagination } from '@/api/types';
import { InfiniteData, QueryClient } from '@tanstack/react-query';

import { isVideo } from '../../../../shared/media-item-utils';

// Patches the already cached pages of the dataset media listing, instead of refetching every page scrolled through.
const updateCachedMedia = (queryClient: QueryClient, updateItem: (item: MediaDTO) => MediaDTO) => {
    queryClient.setQueriesData<InfiniteData<MediaWithPagination>>(
        { queryKey: ['get', '/api/projects/{project_id}/dataset/media'] },
        (oldData) => {
            if (!oldData?.pages) return oldData;

            return {
                ...oldData,
                pages: oldData.pages.map((page) => ({ ...page, items: page.items.map(updateItem) })),
            };
        }
    );
};

export const markCachedMediaAsAnnotated = (queryClient: QueryClient, mediaId: string) => {
    updateCachedMedia(queryClient, (item) =>
        item.id === mediaId && !isVideo(item) ? { ...item, annotation_status: { has_annotations: true } } : item
    );
};

export const replaceCachedMedia = (queryClient: QueryClient, media: MediaDTO) => {
    updateCachedMedia(queryClient, (item) => (item.id === media.id ? media : item));
};

export const refreshCachedMedia = async (queryClient: QueryClient, projectId: string, mediaId: string) => {
    const { data } = await fetchClient.GET('/api/projects/{project_id}/dataset/media/{media_id}', {
        params: { path: { project_id: projectId, media_id: mediaId } },
    });

    if (data !== undefined) {
        replaceCachedMedia(queryClient, data);
    }
};
