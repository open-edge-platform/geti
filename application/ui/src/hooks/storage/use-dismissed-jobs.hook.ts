// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useSessionStorage } from 'usehooks-ts';

export const DISMISSED_JOBS_KEY = 'dismissed-jobs';

export const useDismissedJobs = () => {
    const [dismissedJobIds, setDismissedJobIds] = useSessionStorage<string[]>(DISMISSED_JOBS_KEY, []);

    const dismissJob = (jobId: string): void => {
        setDismissedJobIds((prevState) => (prevState.includes(jobId) ? prevState : [...prevState, jobId]));
    };

    const isJobDismissed = (jobId: string): boolean => dismissedJobIds.includes(jobId);

    return { dismissJob, isJobDismissed };
};
