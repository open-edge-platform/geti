// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ACTIVE_JOB_STATUSES, useModelJobs, useStreamJobStatus } from 'hooks/api/jobs/jobs.hook';

const JobStreamSync = ({ jobId }: { jobId: string }) => {
    useStreamJobStatus(jobId);
    return null;
};

export const ActiveJobsSync = () => {
    const { data: jobs = [] } = useModelJobs();
    const activeJobs = jobs.filter((job) => ACTIVE_JOB_STATUSES.includes(job.status));

    return (
        <>
            {activeJobs.map((job) => (
                <JobStreamSync key={job.job_id} jobId={job.job_id} />
            ))}
        </>
    );
};
