// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import { useQuery } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { $api } from '../api/client';
import type { DatasetItemAnnotationStatus, DatasetSubset, Pagination } from '../api/shared-types';
import { type SortDirection } from './sort-direction.interface';
import { useDatasetFiltersSearchParams } from './use-dataset-filters-search-params.hook';
import { useProjectIdentifier } from './use-project-identifier.hook';

const DATASET_ITEMS_LIMIT = 40;

type SortBy = 'creation_date';

type UseGetDatasetItemsOptions = {
    subsets?: DatasetSubset[];
    annotationStatus?: DatasetItemAnnotationStatus;
    sortDirection?: SortDirection;
    labelIds?: string[];
    startDate?: string;
    endDate?: string;
};

const getDatasetItemsQueryOptions = ({
    subsets,
    annotationStatus,
    sortDirection,
    projectId,
    labelIds,
    startDate,
    endDate,
}: UseGetDatasetItemsOptions & { projectId: string }) => {
    const query: {
        offset: number;
        limit: number;
        subsets?: DatasetSubset[];
        annotation_status?: DatasetItemAnnotationStatus;
        sort_direction?: SortDirection;
        sort_by?: SortBy;
        labels?: string[];
        start_date?: string;
        end_date?: string;
    } = {
        offset: 0,
        limit: DATASET_ITEMS_LIMIT,
    };

    if (!isEmpty(subsets)) {
        query.subsets = subsets;
    }

    if (annotationStatus !== undefined) {
        query.annotation_status = annotationStatus;
    }

    if (sortDirection !== undefined) {
        query.sort_direction = sortDirection;
        query.sort_by = 'creation_date';
    }

    if (!isEmpty(labelIds)) {
        query.labels = labelIds;
    }

    if (startDate !== undefined) {
        query.start_date = startDate;
    }

    if (endDate !== undefined) {
        query.end_date = endDate;
    }

    return $api.queryOptions('get', '/api/projects/{project_id}/dataset/items', {
        params: {
            query,
            path: { project_id: projectId },
        },
    });
};

export const useFetchNextUnannotatedMediaItem = () => {
    const projectId = useProjectIdentifier();

    const { selectedSubsets, sortDirection, selectedLabelIds, startDate, endDate } = useDatasetFiltersSearchParams();
    const queryOptions = getDatasetItemsQueryOptions({
        subsets: selectedSubsets,
        annotationStatus: 'missing_annotations',
        sortDirection,
        labelIds: selectedLabelIds,
        startDate: startDate ?? undefined,
        endDate: endDate ?? undefined,
        projectId,
    });

    return useQuery(queryOptions);
};

export const useGetDatasetItems = ({
    subsets,
    annotationStatus,
    sortDirection,
    labelIds,
    startDate,
    endDate,
}: UseGetDatasetItemsOptions = {}) => {
    const project_id = useProjectIdentifier();

    const query: {
        offset: number;
        limit: number;
        subsets?: DatasetSubset[];
        annotation_status?: DatasetItemAnnotationStatus;
        sort_direction?: SortDirection;
        sort_by?: SortBy;
        labels?: string[];
        start_date?: string;
        end_date?: string;
    } = {
        offset: 0,
        limit: DATASET_ITEMS_LIMIT,
    };

    if (!isEmpty(subsets)) {
        query.subsets = subsets;
    }

    if (annotationStatus !== undefined) {
        query.annotation_status = annotationStatus;
    }

    if (sortDirection !== undefined) {
        query.sort_direction = sortDirection;
        query.sort_by = 'creation_date';
    }

    if (!isEmpty(labelIds)) {
        query.labels = labelIds;
    }

    if (startDate !== undefined) {
        query.start_date = startDate;
    }

    if (endDate !== undefined) {
        query.end_date = endDate;
    }

    const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isPending } = $api.useInfiniteQuery(
        'get',
        '/api/projects/{project_id}/dataset/items',
        {
            params: {
                query,
                path: { project_id },
            },
        },
        {
            pageParamName: 'offset',
            getNextPageParam: ({ pagination }: { pagination: Pagination }) => {
                const total = pagination.offset + pagination.count;

                if (total >= pagination.total) {
                    return undefined;
                }

                return pagination.offset + DATASET_ITEMS_LIMIT;
            },
        }
    );

    const items = useMemo(() => {
        return data?.pages.flatMap((page) => page.items) ?? [];
    }, [data?.pages]);

    const totalCount = data?.pages[0]?.pagination?.total ?? 0;

    return { items, fetchNextPage, hasNextPage, isFetchingNextPage, isPending, totalCount };
};
