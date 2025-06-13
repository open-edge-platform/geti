// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { ActionButton, Loading, Text } from '@geti/ui';
import { Delete } from '@geti/ui/icons';
import { UseMutationResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import clsx from 'clsx';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Job } from '../../../../core/jobs/jobs.interface';
import { isJobTrain } from '../../../../core/jobs/utils';
import { CustomAlertDialog } from '../../alert-dialog/custom-alert-dialog.component';
import { TooltipWithDisableButton } from '../../custom-tooltip/tooltip-with-disable-button';
import { JobCancellationWarning } from './jobs-cancellation-warning.component';
import { DISCARD_TYPE, isCancellableJob, isJobRunning } from './utils';

import classes from './jobs.module.scss';

interface JobsDiscardActionProps {
    job: Job;
    discardType: DISCARD_TYPE;
    useDeleteJob: UseMutationResult<string, AxiosError, string, unknown>;
    useCancelJob: UseMutationResult<string, AxiosError, string, unknown>;
}

const ButtonIcon = ({ isLoading, isCancel }: { isLoading: boolean; isCancel: boolean }) => {
    if (isLoading) {
        return <Loading mode='inline' size='S' marginX='size-100' />;
    }

    if (isCancel) {
        return <Text>{DISCARD_TYPE.CANCEL}</Text>;
    }

    return <Delete aria-label={'Delete job'} />;
};

export const JobsDiscardAction = ({
    job,
    discardType,
    useDeleteJob,
    useCancelJob,
}: JobsDiscardActionProps): JSX.Element => {
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const [dialogOpen, setDialogOpen] = useState<boolean>(false);

    const isCancel = discardType === DISCARD_TYPE.CANCEL;
    const totalCreditsConsumed = job.cost?.consumed.reduce((total, current) => total + current.amount, 0) || 0;
    const displayJobCancellationWarning = FEATURE_FLAG_CREDIT_SYSTEM && isJobTrain(job) && totalCreditsConsumed > 0;

    const isNotCancellableRunningJob = isJobRunning(job) && !isCancellableJob(job);

    const isDisabledDeleteButton = useDeleteJob.isPending || useDeleteJob.isSuccess;
    const isDisabledCancelButton = useCancelJob.isPending || useCancelJob.isSuccess || isNotCancellableRunningJob;
    const isPrimaryActionDisabled = isDisabledCancelButton || isDisabledDeleteButton;

    const cancelJob = () => useCancelJob.mutate(job.id);
    const deleteJob = () => useDeleteJob.mutate(job.id);

    const action = () => {
        setDialogOpen(false);

        isCancel ? cancelJob() : deleteJob();
    };

    return (
        <>
            <TooltipWithDisableButton disabledTooltip={'For data consistency reasons, this job cannot be cancelled.'}>
                <ActionButton
                    isQuiet
                    onPress={() => setDialogOpen(true)}
                    isDisabled={isPrimaryActionDisabled}
                    id={`job-scheduler-${job.id}-action-${discardType.toLowerCase()}`}
                    data-testid={`job-scheduler-${job.id}-action-${discardType.toLowerCase()}`}
                    UNSAFE_className={clsx({ [classes.discardActionLink]: isCancel })}
                >
                    <ButtonIcon isCancel={isCancel} isLoading={useDeleteJob.isPending || useCancelJob.isPending} />
                </ActionButton>
            </TooltipWithDisableButton>

            {discardType === DISCARD_TYPE.CANCEL ? (
                <JobCancellationWarning
                    jobName={job.name}
                    totalCreditsConsumed={totalCreditsConsumed}
                    shouldShowLostCreditsContent={displayJobCancellationWarning}
                    isOpen={dialogOpen}
                    setIsOpen={setDialogOpen}
                    onPrimaryAction={action}
                    isPrimaryActionDisabled={isPrimaryActionDisabled}
                />
            ) : (
                <CustomAlertDialog
                    open={dialogOpen}
                    setOpen={setDialogOpen}
                    onPrimaryAction={action}
                    primaryActionLabel='Delete'
                    isPrimaryActionDisabled={isPrimaryActionDisabled}
                    cancelLabel={'Back'}
                    title={'Delete job'}
                    message={`Are you sure you want to delete job "${job.name}"?`}
                    cancelButtonAriaLabel={`Close delete job dialog`}
                    primaryActionButtonAriaLabel='Delete job'
                    id={`delete-job-dialog`}
                />
            )}
        </>
    );
};
