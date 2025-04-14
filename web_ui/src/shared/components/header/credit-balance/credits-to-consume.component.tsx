// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
