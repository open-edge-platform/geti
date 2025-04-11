// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { InfiniteData } from '@tanstack/react-query';

import { GETI_SYSTEM_AUTHOR_ID, JobState } from '../../../core/jobs/jobs.const';
import { Job } from '../../../core/jobs/jobs.interface';
import { JobsResponse } from '../../../core/jobs/services/jobs-service.interface';

export const enum JOB_TRIGGER {
    MANUAL = 'manual',
    AUTO = 'auto',
}

export const onScheduledTrainingJobs =
    (callback: (scheduledJob: Job) => void, trigger: JOB_TRIGGER) =>
    ({ pages }: InfiniteData<JobsResponse>) => {
        if (!pages[0]) {
            return;
        }
        const { jobs, jobsCount } = pages[0];
        const totalScheduledJobs = Number(jobsCount.numberOfScheduledJobs);
        const scheduledAutoTrainingJob = jobs.find((job) => {
            return job.state === JobState.SCHEDULED && job.authorId === GETI_SYSTEM_AUTHOR_ID;
        });
        const scheduledManualTrainingJob = jobs.find((job) => {
            return job.state === JobState.SCHEDULED && job.authorId !== GETI_SYSTEM_AUTHOR_ID;
        });
        const hasScheduledTrainingJobs = totalScheduledJobs > 0;

        // Note: Requested trigger (manual/auto) must match scheduled job's author (user/auto)

        if (trigger === JOB_TRIGGER.AUTO && scheduledAutoTrainingJob && hasScheduledTrainingJobs) {
            callback(scheduledAutoTrainingJob);
        }

        if (trigger === JOB_TRIGGER.MANUAL && scheduledManualTrainingJob && hasScheduledTrainingJobs) {
            callback(scheduledManualTrainingJob);
        }
    };
