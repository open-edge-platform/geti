// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { getAllJobs } from '@shared/components/header/jobs-management/utils';

import { useGetRunningJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { Job } from '../../../../core/jobs/jobs.interface';
import { getJobActiveStep } from '../../../../core/jobs/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { Footer as CommonFooter } from './annotator-footer.component';
import { TrainingProgress } from './training-progress/training-progress.component';

export const Footer = (): JSX.Element => {
    const { projectIdentifier } = useProject();
    const { selectedMediaItem } = useSelectedMediaItem();
    const { selectedTask } = useTask();
    const runningJobsQuery = useGetRunningJobs({ projectId: projectIdentifier.projectId, selectedTask });

    const trainingJobs = getAllJobs(runningJobsQuery.data);

    const isJobForTask = (job: Job) => {
        // @ts-expect-error A training job contains metadata for its associated task
        return job.metadata?.task?.taskId === selectedTask.id;
    };

    const currentTrainingJob = trainingJobs.find((job) => {
        return selectedTask !== null ? isJobForTask(job) : true;
    });

    const jobTrainingStatus = useMemo(() => {
        if (currentTrainingJob === undefined) {
            return {
                message: 'Waiting for user annotations',
                progress: undefined,
            };
        }

        const activeStep = getJobActiveStep(currentTrainingJob);

        const progress = activeStep?.progress ?? 0;

        return {
            message: activeStep?.message ?? 'Waiting for user annotations',
            progress,
        };
    }, [currentTrainingJob]);

    return (
        <CommonFooter selectedItem={selectedMediaItem} gridArea='footer' areActionsDisabled>
            <TrainingProgress training={jobTrainingStatus} />
        </CommonFooter>
    );
};
