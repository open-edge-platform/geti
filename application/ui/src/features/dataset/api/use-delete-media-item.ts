// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { useTranslation } from '@/i18n';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { useOverlayTriggerState } from 'react-stately';

import { getQueryKey } from '../../../query-client/query-client';

const toastId = 'deleting-notification';

const useDeleteMediaItemsMutation = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const projectId = useProjectIdentifier();

    return $api.useMutation('delete', `/api/projects/{project_id}/dataset/media`, {
        meta: { error: { notify: () => false } },
        onSuccess: () =>
            Promise.all([
                queryClient.invalidateQueries({
                    queryKey: getQueryKey([
                        'get',
                        '/api/projects/{project_id}/dataset/statistics',
                        { params: { path: { project_id: projectId } } },
                    ]),
                }),
                queryClient.invalidateQueries({
                    queryKey: getQueryKey([
                        'get',
                        '/api/projects/{project_id}/dataset/media',
                        { params: { path: { project_id: projectId } } },
                    ]),
                }),
            ]),
        onError: (error) => {
            toast({
                id: toastId,
                type: 'error',
                message: t('dataset.delete.deleteError', { detail: error?.detail }),
            });
        },
    });
};

export const useDeleteMediaItem = () => {
    const { t } = useTranslation();
    const projectId = useProjectIdentifier();
    const deleteItemsMutation = useDeleteMediaItemsMutation();

    const alertDialogState = useOverlayTriggerState({});

    const handleDeleteItems = (media_ids: string[], onDeleted?: (ids: string[]) => void) => {
        alertDialogState.close();

        toast({ id: toastId, type: 'info', message: t('dataset.delete.deletingItems') });

        deleteItemsMutation.mutate(
            {
                body: { media_ids },
                params: { path: { project_id: projectId } },
            },
            {
                onSuccess: () => {
                    onDeleted?.(media_ids);
                    toast({
                        id: toastId,
                        type: 'success',
                        message: t('dataset.delete.deletedSuccess', { count: media_ids.length }),
                        duration: 3000,
                    });
                },
            }
        );
    };

    return {
        deleteMedia: handleDeleteItems,
        isPending: deleteItemsMutation.isPending,
        isDeleteDialogOpen: alertDialogState.isOpen,
        openDeleteDialog: alertDialogState.open,
        closeDeleteDialog: alertDialogState.close,
    };
};
