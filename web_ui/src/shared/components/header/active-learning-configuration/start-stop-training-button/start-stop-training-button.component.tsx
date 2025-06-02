// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Button, Loading } from '@geti/ui';
import { head } from 'lodash-es';

import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { RunningTrainingJob } from '../../../../../core/jobs/jobs.interface';
import { isJobTrain } from '../../../../../core/jobs/utils';
import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { Task } from '../../../../../core/projects/task.interface';
import { CreditBalanceTrainDialog } from '../../../../../pages/project-details/components/project-models/train-model-dialog/credit-balance-train-dialog.component';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { JobCancellationWarning } from '../../jobs-management/jobs-cancellation-warning.component';

interface ToggleTrainingButtonProps {
    task: Task;
    isAutotraining: boolean;
    runningTaskJobs: RunningTrainingJob[];
    projectIdentifier: ProjectIdentifier;
}

export const ToggleTrainingButton = ({
    task,
    runningTaskJobs,
    isAutotraining,
    projectIdentifier,
}: ToggleTrainingButtonProps): JSX.Element => {
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const job = head(runningTaskJobs.filter(isJobTrain));
    const totalCreditsConsumed = job?.cost?.consumed.reduce((total, current) => total + current.amount, 0) || 0;
    const showCostDialog = FEATURE_FLAG_CREDIT_SYSTEM && job && !!totalCreditsConsumed;
    const [isTrainingDialogOpen, setIsTrainingDialogOpen] = useState(false);
    const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
    const { useTrainModelMutation } = useModels();
    const trainModel = useTrainModelMutation();
    const { useCancelJob } = useJobs(projectIdentifier);

    const onCancelJob = () => {
        setIsCancelDialogOpen(false);
        if (job) useCancelJob.mutate(job.id);
    };

    return (
        <>
            {!job && (
                <Button
                    variant='primary'
                    aria-label={`start training ${task.title} task`}
                    onPress={() => setIsTrainingDialogOpen(true)}
                    isDisabled={trainModel.isPending || isAutotraining}
                    id={`start-training-${idMatchingFormat(task.title)}`}
                >
                    {trainModel.isPending && <Loading mode="inline" size={'S'} marginX={'size-100'} />}
                    Start training now
                </Button>
            )}

            {!!job && (
                <Button
                    variant='secondary'
                    isDisabled={useCancelJob.isPending}
                    onPress={() => setIsCancelDialogOpen(true)}
                    id={`stop-training-${idMatchingFormat(task.title)}`}
                >
                    {useCancelJob.isPending && <Loading mode="inline" size={'S'} marginX={'size-100'} />}
                    Stop training
                </Button>
            )}
            <CreditBalanceTrainDialog
                task={task}
                isOpen={isTrainingDialogOpen}
                onClose={() => setIsTrainingDialogOpen(false)}
            />
            <JobCancellationWarning
                totalCreditsConsumed={totalCreditsConsumed}
                jobName={job?.name}
                isOpen={isCancelDialogOpen}
                setIsOpen={setIsCancelDialogOpen}
                onPrimaryAction={onCancelJob}
                shouldShowLostCreditsContent={!!showCostDialog}
                isPrimaryActionDisabled={useCancelJob.isPending}
            />
        </>
    );
};
