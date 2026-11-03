// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import type { DatasetItemAnnotationStatus, DatasetSubset } from '@/api/types';

import { type SortDirection } from './sort-direction.interface';
import { useGetDatasetItems } from './use-get-dataset-items.hook';

type UseGetDatasetItemsByIdOptions = {
    annotationStatus?: DatasetItemAnnotationStatus;
    sortDirection?: SortDirection;
    subsets?: DatasetSubset[];
    labelIds?: string[];
    startDate?: string;
    endDate?: string;
    datasetViewId?: string;
};

export const useGetDatasetItemsById = ({
    annotationStatus,
    sortDirection,
    subsets,
    labelIds,
    startDate,
    endDate,
    datasetViewId,
}: UseGetDatasetItemsByIdOptions) => {
    const datasetItemsQuery = useGetDatasetItems({
        annotationStatus,
        sortDirection,
        subsets,
        labelIds,
        startDate,
        endDate,
        datasetViewId,
    });

    const reviewStatus = useMemo(() => {
        const entries = datasetItemsQuery.items.map(({ id, user_reviewed }) => [id, user_reviewed] as const);

        return new Map(entries);
    }, [datasetItemsQuery.items]);

    return { reviewStatus, ...datasetItemsQuery };
};
