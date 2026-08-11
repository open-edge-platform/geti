// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import { $api } from '@/api';
import type { DatasetItemAnnotationStatus, DatasetSubset, Pagination } from '@/api/types';
import { isEmpty } from 'lodash-es';

import { type SortDirection } from './sort-direction.interface';
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
    limit?: number;
};

const getDatasetItemsQueryParameter = ({
    subsets,
    annotationStatus,
    sortDirection,
    labelIds,
    startDate,
    endDate,
    limit = DATASET_ITEMS_LIMIT,
}: UseGetDatasetItemsOptions) => {
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
        limit,
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

    return query;
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

    const query = getDatasetItemsQueryParameter({
        subsets,
        annotationStatus,
        sortDirection,
        labelIds,
        startDate,
        endDate,
    });

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
        return data?.pages?.flatMap((page) => page.items) ?? [];
    }, [data?.pages]);

    const totalCount = data?.pages[0]?.pagination?.total ?? 0;

    return { items, fetchNextPage, hasNextPage, isFetchingNextPage, isPending, totalCount };
};
