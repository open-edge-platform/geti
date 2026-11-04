// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fetchClient } from '@/api';
import type { MediaDTO, MediaWithPagination } from '@/api/types';
import { InfiniteData, Query, QueryClient } from '@tanstack/react-query';
import type { DatasetMediaQueryFilters } from 'hooks/use-get-dataset-media-items.hook';
import { isEmpty } from 'lodash-es';

import { getQueryKey } from '../../../../query-client/query-client';
import { isVideo } from '../../../../shared/media-item-utils';

const getDatasetMediaQueryKey = (projectId: string) =>
    getQueryKey(['get', '/api/projects/{project_id}/dataset/media', { params: { path: { project_id: projectId } } }]);

// Saving annotations can change whether a media matches these filters
const ANNOTATION_DEPENDENT_FILTERS = ['annotation_status', 'labels', 'subsets'] as const;

type DatasetMediaQueryKey = readonly [string, string, { params?: { query?: DatasetMediaQueryFilters } }?];

const isFilteredByAnnotations = (query: Query): boolean => {
    const [, , init] = query.queryKey as DatasetMediaQueryKey;
    const filters = init?.params?.query ?? {};

    return ANNOTATION_DEPENDENT_FILTERS.some((filter) => !isEmpty(filters[filter]));
};

/**
 * Refetches the dataset media listings filtered by annotation status, labels or subsets, since saved annotations may
 * add media to them or remove media from them. Removing the item locally would shift the offset-based pages instead.
 */
export const invalidateMediaFilteredByAnnotations = (queryClient: QueryClient, projectId: string) =>
    queryClient.invalidateQueries({
        queryKey: getDatasetMediaQueryKey(projectId),
        predicate: isFilteredByAnnotations,
    });

// Patches the already cached pages of the other dataset media listings, instead of refetching every page scrolled
// through: their content does not depend on annotations.
const updateCachedMedia = (queryClient: QueryClient, projectId: string, updateItem: (item: MediaDTO) => MediaDTO) => {
    queryClient.setQueriesData<InfiniteData<MediaWithPagination>>(
        { queryKey: getDatasetMediaQueryKey(projectId), predicate: (query) => !isFilteredByAnnotations(query) },
        (oldData) => {
            if (!oldData?.pages) return oldData;

            return {
                ...oldData,
                pages: oldData.pages.map((page) => ({ ...page, items: page.items.map(updateItem) })),
            };
        }
    );
};

export const markCachedMediaAsAnnotated = (queryClient: QueryClient, projectId: string, mediaId: string) => {
    // Any successful save annotates the media: an empty annotation list is stored as the "no objects" annotation
    // (empty label), which the server reports as `has_annotations: true`.
    updateCachedMedia(queryClient, projectId, (item) =>
        item.id === mediaId && !isVideo(item) ? { ...item, annotation_status: { has_annotations: true } } : item
    );
};

const replaceCachedMedia = (queryClient: QueryClient, projectId: string, media: MediaDTO) => {
    updateCachedMedia(queryClient, projectId, (item) => (item.id === media.id ? media : item));
};

export const refreshCachedMedia = async (queryClient: QueryClient, projectId: string, mediaId: string) => {
    const { data } = await fetchClient.GET('/api/projects/{project_id}/dataset/media/{media_id}', {
        params: { path: { project_id: projectId, media_id: mediaId } },
    });

    if (data !== undefined) {
        replaceCachedMedia(queryClient, projectId, data);
    }
};
