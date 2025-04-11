// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import { useGetRunningJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { Job } from '../../../../core/jobs/jobs.interface';
import { getJobActiveStep } from '../../../../core/jobs/utils';
import { getAllJobs } from '../../../../shared/components/header/jobs-management/utils';
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
