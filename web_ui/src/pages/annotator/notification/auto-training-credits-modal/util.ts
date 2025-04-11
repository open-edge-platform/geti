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

import { GETI_SYSTEM_AUTHOR_ID, JobState } from '../../../../core/jobs/jobs.const';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserGlobalSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getFuxSetting } from '../../../../shared/components/tutorials/utils';

export const onFirstScheduledAutoTrainingJob =
    (settings: UseSettings<UserGlobalSettings>, callback: (jobId: string) => void) =>
    ({ pages }: InfiniteData<JobsResponse>) => {
        if (!pages[0]) {
            return;
        }

        const { jobs, jobsCount } = pages[0];
        const totalScheduledJobs = Number(jobsCount.numberOfScheduledJobs);
        const hasScheduleTrainingJobs = totalScheduledJobs > 0;
        const neverAutotrained = getFuxSetting(FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED, settings.config);
        const isAutoTrainingJob = jobs.find((job) => {
            return job.state === JobState.SCHEDULED && job.authorId === GETI_SYSTEM_AUTHOR_ID;
        });

        if (hasScheduleTrainingJobs && neverAutotrained && isAutoTrainingJob) {
            const jobId = isAutoTrainingJob.id;
            callback(jobId);
        }
    };
