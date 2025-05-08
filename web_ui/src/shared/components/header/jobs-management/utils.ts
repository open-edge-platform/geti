// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteData } from '@tanstack/react-query';
import dayjs from 'dayjs';
import durationPlugin from 'dayjs/plugin/duration.js';
import { isNil, overSome } from 'lodash-es';

import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { Job, JobExportStatus, RunningTrainingJob } from '../../../../core/jobs/jobs.interface';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { isJobDatasetExport, isJobProjectExport } from '../../../../core/jobs/utils';

dayjs.extend(durationPlugin);

export enum DISCARD_TYPE {
    CANCEL = 'Cancel',
    DELETE = 'Delete',
}

export const JOB_STATE_TO_DISCARD_TYPE: Record<JobState, DISCARD_TYPE | undefined> = {
    [JobState.RUNNING]: DISCARD_TYPE.CANCEL,
    [JobState.FINISHED]: DISCARD_TYPE.DELETE,
    [JobState.SCHEDULED]: DISCARD_TYPE.CANCEL,
    [JobState.FAILED]: DISCARD_TYPE.DELETE,
    [JobState.CANCELLED]: DISCARD_TYPE.DELETE,
};

export const getNameFromJob = (name: string): string => {
    const index: number = name.indexOf('task') - 1;

    return index >= 0 ? name.slice(0, index) : name;
};

export const getStepProgress = (progress: number | null | undefined): string => {
    if (isNil(progress) || progress < 0) return '';

    return `${Math.round(Number(progress))}%`;
};

export const getStepProgressNumber = (progress: number | null | undefined): number => {
    return !isNil(progress) && progress > 0 ? progress : 0;
};

export const isJobRunning = (job?: Pick<Job, 'state'>) => job?.state === JobState.RUNNING;
export const isJobScheduled = (job?: Pick<Job, 'state'>): boolean => job?.state === JobState.SCHEDULED;
export const isJobDone = (job?: Pick<Job, 'state'>): boolean => job?.state === JobState.FINISHED;
export const isJobFailed = (job?: Pick<Job, 'state'>): boolean => job?.state === JobState.FAILED;
export const isJobCancel = (job?: Pick<Job, 'state'>): boolean => job?.state === JobState.CANCELLED;
export const isJobCancelOrFailed = overSome([isJobFailed, isJobCancel]);
export const isJobSettled = overSome([isJobDone, isJobCancelOrFailed]);

export const isJobExportDone = (job: Job): job is JobExportStatus =>
    (isJobDatasetExport(job) || isJobProjectExport(job)) && isJobDone(job);

export const isRunningTrainingJob = (job?: Job): job is RunningTrainingJob =>
    isJobRunning(job) && job?.type === JobType.TRAIN;

export const isCancellableJob = (job: Job): boolean => job.cancellationInfo.isCancellable;

export const getAllJobs = (data?: InfiniteData<JobsResponse>) =>
    data?.pages?.flatMap((jobsResponse) => jobsResponse.jobs) ?? [];

const MINUTE_IN_SECONDS = 60 as number;
const HOUR_IN_SECONDS = 3600 as number;
const DAY_IN_SECONDS = 86400 as number;

export const formatJobDuration = (durationInSeconds: number): string => {
    const duration = durationInSeconds < 0 ? 0 : durationInSeconds;
    const durationObject = dayjs.duration(duration, 'seconds');

    if (duration < MINUTE_IN_SECONDS) {
        return `${durationObject.format('s [sec]')}`;
    }
    if (duration < HOUR_IN_SECONDS) {
        if (duration === MINUTE_IN_SECONDS) {
            return `${durationObject.format('m [min]')}`;
        }

        return `${durationObject.format('m [min], s [sec]')}`;
    }

    if (duration === HOUR_IN_SECONDS) {
        return `${durationObject.format('H [hr]')}`;
    }

    if (duration < DAY_IN_SECONDS) {
        return `${durationObject.format('H [hr], m [min], s [sec]')}`;
    }

    if (duration === DAY_IN_SECONDS) {
        return `${durationObject.format('D [d]')}`;
    }

    return `${durationObject.format('D [d], H [hr]')}`;
};

export const getJobDuration = (job: Job): string | undefined => {
    const isFinishedJob = isJobDone(job);

    if (!isFinishedJob || job.endTime === null || job.startTime === null) {
        return undefined;
    }

    const endTime = new Date(job.endTime).getTime();
    const startTime = new Date(job.startTime).getTime();

    return formatJobDuration((endTime - startTime) / 1000);
};
