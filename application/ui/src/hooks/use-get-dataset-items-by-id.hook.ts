// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo, useRef } from 'react';

import type { DatasetItemAnnotationStatus, DatasetSubset } from '../constants/shared-types';
import { type SortDirection } from './sort-direction.interface';
import { useGetDatasetItems } from './use-get-dataset-items.hook';

type UseGetDatasetItemsByIdOptions = {
    annotationStatus?: DatasetItemAnnotationStatus;
    sortDirection?: SortDirection;
    subsets?: DatasetSubset[];
    labelIds?: string[];
    startDate?: string;
    endDate?: string;
};

export const useGetDatasetItemsById = ({ annotationStatus, sortDirection, subsets }: UseGetDatasetItemsByIdOptions) => {
    const { items, ...response } = useGetDatasetItems({ annotationStatus, sortDirection, subsets });

    const accumulatedReviewStatusRef = useRef(new Map<string, boolean>());

    const reviewStatus = useMemo(() => {
        items.forEach(({ id, user_reviewed }) => {
            accumulatedReviewStatusRef.current.set(id, user_reviewed);
        });

        return new Map(accumulatedReviewStatusRef.current);
    }, [items]);

    return { reviewStatus, ...response };
};
