// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { AlertDialog, Button, DialogTrigger } from '@geti-ui/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isInvalidJob } from 'hooks/api/util';
import { useTranslation } from 'react-i18next';

type CancelJobConfirmationProps = {
    jobId: string;
    onRemove: () => void | Promise<void>;
};

export const CancelJobConfirmation = ({ jobId, onRemove }: CancelJobConfirmationProps) => {
    const { t } = useTranslation();

    const dialogState = useOverlayTriggerState({});
    const cancelMutation = $api.useMutation('post', `/api/jobs/{job_id}:cancel`);

    const handleCancel = () => {
        cancelMutation.mutate(
            { params: { path: { job_id: jobId } } },
            {
                onSuccess: async () => await onRemove(),
                onError: async (error) => {
                    isInvalidJob(error) && (await onRemove());
                },
                onSettled: () => {
                    dialogState.close();
                },
            }
        );
    };

    return (
        <DialogTrigger>
            <Button
                variant='negative'
                style='outline'
                aria-label={t('dataset.cancelJobAriaLabel')}
                isDisabled={cancelMutation.isPending}
                isPending={cancelMutation.isPending}
            >
                {t('dataset.cancelJobButton')}
            </Button>
            <AlertDialog
                title={t('dataset.cancelJobTitle')}
                variant='destructive'
                cancelLabel={t('common.cancel')}
                autoFocusButton='primary'
                primaryActionLabel={t('dataset.cancelJobAction')}
                onPrimaryAction={handleCancel}
                onSecondaryAction={dialogState.close}
                isPrimaryActionDisabled={cancelMutation.isPending}
            >
                {t('dataset.cancelJobConfirmText', { jobId })}
            </AlertDialog>
        </DialogTrigger>
    );
};
