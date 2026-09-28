// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { fetchClient } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { useTranslation } from '@/i18n';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { chunk, isEmpty, partition } from 'lodash-es';

import { getQueryKey } from '../../../../../query-client/query-client';
import { filterOutEmptyLabels } from '../../../../../shared/labels';

// Annotations can only be set one media at a time, so cap how many requests are in flight at once.
const ASSIGN_LABEL_BATCH_SIZE = 10;

export const useBulkAssignLabel = () => {
    const { t } = useTranslation();
    const projectId = useProjectIdentifier();
    const queryClient = useQueryClient();

    // Tracks the whole batched run, which a per-request mutation state could not: it would only
    // follow the request dispatched last and flicker as each batch settles.
    const [isPending, setIsPending] = useState(false);

    const invalidateQueries = () => {
        queryClient.invalidateQueries({
            queryKey: getQueryKey([
                'get',
                '/api/projects/{project_id}/dataset/items',
                { params: { path: { project_id: projectId } } },
            ]),
        });
        queryClient.invalidateQueries({
            queryKey: getQueryKey([
                'get',
                '/api/projects/{project_id}/dataset/media',
                {
                    params: {
                        path: { project_id: projectId },
                    },
                },
            ]),
        });
    };

    const assignLabel = async (mediaId: string, labelIds: string[]) => {
        const labelsWithoutEmptyLabel = filterOutEmptyLabels(labelIds.map((id) => ({ id })));

        const { error } = await fetchClient.POST('/api/projects/{project_id}/dataset/media/{media_id}/annotations', {
            params: {
                path: {
                    project_id: projectId,
                    media_id: mediaId,
                },
            },
            body: {
                annotations: isEmpty(labelsWithoutEmptyLabel)
                    ? []
                    : [{ shape: { type: 'full_image' }, labels: labelsWithoutEmptyLabel }],
            },
        });

        if (error !== undefined) {
            throw error;
        }
    };

    const bulkAssignLabel = async (mediaIds: string[], labelIds: string[]) => {
        setIsPending(true);

        try {
            const result: PromiseSettledResult<void>[] = [];

            for (const batch of chunk(mediaIds, ASSIGN_LABEL_BATCH_SIZE)) {
                result.push(...(await Promise.allSettled(batch.map((mediaId) => assignLabel(mediaId, labelIds)))));
            }

            const [successfulMediaItems, failedMediaItems] = partition(result, ({ status }) => status === 'fulfilled');

            if (failedMediaItems.length === 0) {
                toast({
                    type: 'success',
                    message: t('dataset.bulkLabels.assignAllSuccess', { count: successfulMediaItems.length }),
                });
            } else if (successfulMediaItems.length === 0) {
                toast({
                    type: 'error',
                    message: t('dataset.bulkLabels.assignAllFailure', { count: failedMediaItems.length }),
                });
            } else {
                toast({
                    type: 'info',
                    message: t('dataset.bulkLabels.assignPartialSuccess', {
                        succeeded: successfulMediaItems.length,
                        total: mediaIds.length,
                        failed: failedMediaItems.length,
                    }),
                });
            }

            invalidateQueries();
        } finally {
            setIsPending(false);
        }
    };

    return {
        mutate: bulkAssignLabel,
        isPending,
    };
};
