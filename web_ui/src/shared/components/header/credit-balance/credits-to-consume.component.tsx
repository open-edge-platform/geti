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

import { useEffect, useState } from 'react';

import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { JobType } from '../../../../core/jobs/jobs.const';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { ThreeDotsFlashing } from '../../three-dots-flashing/three-dots-flashing.component';
import { isJobRunning, isJobScheduled } from '../jobs-management/utils';

import classes from './credits-to-consume.module.scss';

export const CreditsToConsume = () => {
    const { projectIdentifier } = useProject();
    const { useGetJobs } = useJobs(projectIdentifier);
    const [totalCreditsToConsume, setTotalCreditsToConsume] = useState<number | undefined>();

    const { data, isSuccess } = useGetJobs({
        jobTypes: [JobType.TRAIN],
        projectId: projectIdentifier.projectId,
    });

    const job = data?.pages
        .flatMap((page) => page.jobs)
        .filter((j) => isJobScheduled(j) || isJobRunning(j))
        .at(0);

    // Keep track of the total credits that were consumed by this job, and keep it even if the job's state
    // moves to another non `SCHEDULED` or `RUNNING` state so that we don't show 0 credits when job becomes undefined
    useEffect(() => {
        job && setTotalCreditsToConsume(job?.cost?.requests.reduce((acc, curr) => acc + curr.amount, 0));
    }, [job]);

    return (
        <>
            {!isSuccess || !totalCreditsToConsume ? (
                <ThreeDotsFlashing className={classes.threeDotsFlashing} />
            ) : (
                String(totalCreditsToConsume)
            )}
        </>
    );
};
