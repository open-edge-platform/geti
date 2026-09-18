// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { useTranslation } from '@/i18n';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { chunk, isEmpty, partition } from 'lodash-es';

import { getQueryKey } from '../../../../../query-client/query-client';
import { filterOutEmptyLabels } from '../../../../../shared/annotator/labels';

// Annotations can only be set one media at a time, so cap how many requests are in flight at once.
const ASSIGN_LABEL_BATCH_SIZE = 10;

export const useBulkAssignLabel = () => {
    const { t } = useTranslation();
    const projectId = useProjectIdentifier();
    const queryClient = useQueryClient();
    const mutation = $api.useMutation('post', '/api/projects/{project_id}/dataset/media/{media_id}/annotations');

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

        return mutation.mutateAsync({
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
    };

    const bulkAssignLabel = async (mediaIds: string[], labelIds: string[]) => {
        const result: PromiseSettledResult<Awaited<ReturnType<typeof assignLabel>>>[] = [];

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
    };

    return {
        mutate: bulkAssignLabel,
        isPending: mutation.isPending,
    };
};
