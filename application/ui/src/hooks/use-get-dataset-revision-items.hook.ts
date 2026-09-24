// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import type { DatasetRevisionItem, DatasetSubset, Pagination } from '@/api/types';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEmpty } from 'lodash-es';

const DATASET_ITEMS_LIMIT = 20;

interface UseGetDatasetRevisionItemsOptions {
    datasetRevisionId: string;
    subsets?: DatasetSubset[];
}

export const useGetDatasetRevisionItems = ({ datasetRevisionId, subsets }: UseGetDatasetRevisionItemsOptions) => {
    const project_id = useProjectIdentifier();

    const query = !isEmpty(subsets)
        ? { offset: 0, limit: DATASET_ITEMS_LIMIT, subsets }
        : { offset: 0, limit: DATASET_ITEMS_LIMIT };

    const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isPending } = $api.useInfiniteQuery(
        'get',
        '/api/projects/{project_id}/dataset_revisions/{dataset_revision_id}/items',
        {
            params: {
                query,
                path: { project_id, dataset_revision_id: datasetRevisionId },
            },
        },
        {
            pageParamName: 'offset',
            initialPageParam: 0,
            getNextPageParam: ({ pagination }: { pagination: Pagination }) => {
                const total = pagination.offset + pagination.count;

                if (total >= pagination.total) {
                    return undefined;
                }

                return pagination.offset + DATASET_ITEMS_LIMIT;
            },
        }
    );

    const items: DatasetRevisionItem[] = data?.pages.flatMap((page) => page.items) ?? [];
    const totalCount = data?.pages[0]?.pagination?.total ?? 0;

    return { items, fetchNextPage, hasNextPage, isFetchingNextPage, isPending, totalCount };
};
