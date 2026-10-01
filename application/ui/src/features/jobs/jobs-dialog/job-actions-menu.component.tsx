// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { useTranslation } from '@/i18n';
import { ActionMenu, AlertDialog, DialogContainer, Item, type Key } from '@geti-ui/ui';
import { useCancelJob } from 'hooks/api/jobs/jobs.hook';
import { isJobPending, isJobRunning } from 'hooks/api/util';

import type { ModelJob } from '../utils';

const ACTIONS = {
    LOGS: 'logs',
    CANCEL: 'cancel',
};

interface JobActionsMenuProps {
    job: ModelJob;
    onViewLogs: () => void;
}

export const JobActionsMenu = ({ job, onViewLogs }: JobActionsMenuProps) => {
    const { t } = useTranslation();
    const cancelJobMutation = useCancelJob();
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);

    const canCancel = isJobPending(job) || isJobRunning(job);

    const handleAction = (key: Key) => {
        if (key === ACTIONS.LOGS) onViewLogs();
        if (key === ACTIONS.CANCEL) setIsConfirmOpen(true);
    };

    const handleCancel = () => {
        cancelJobMutation.mutate(
            { params: { path: { job_id: job.job_id } } },
            { onSuccess: () => setIsConfirmOpen(false) }
        );
    };

    return (
        <>
            <ActionMenu isQuiet aria-label={`Job actions for ${job.metadata.model.name}`} onAction={handleAction}>
                {[
                    <Item key={ACTIONS.LOGS}>{t('jobs.actions.viewLogs')}</Item>,
                    ...(canCancel ? [<Item key={ACTIONS.CANCEL}>{t('common.actions.cancel')}</Item>] : []),
                ]}
            </ActionMenu>

            <DialogContainer onDismiss={() => setIsConfirmOpen(false)}>
                {isConfirmOpen && (
                    <AlertDialog
                        title={t('jobs.cancel.title')}
                        variant='destructive'
                        primaryActionLabel={t('jobs.cancel.title')}
                        onPrimaryAction={handleCancel}
                        isPrimaryActionDisabled={cancelJobMutation.isPending}
                        cancelLabel={t('common.actions.dismiss')}
                    >
                        {t('jobs.cancel.confirmation', { jobId: job.job_id })}
                    </AlertDialog>
                )}
            </DialogContainer>
        </>
    );
};
