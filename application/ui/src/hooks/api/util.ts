// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Job, QuantizeJob, TrainJob } from '@/api/types';
import type { TranslateFn } from '@/i18n';
import isObject from 'lodash-es/isObject';

const INVALID_STAGED_FILE_REGEX = /^Staged dataset.*not found\.?$/i;

export const isInvalidStagedFile = (error: unknown): boolean => {
    if (isObject(error) && 'detail' in error) {
        const detail = String(error.detail).trim();
        return INVALID_STAGED_FILE_REGEX.test(detail);
    }

    return false;
};

export const getJobProgress = (progress?: number) => Math.round(Math.max(0, Math.min(100, progress ?? 0)));

const JOB_STATUS_KEYS = {
    PENDING: 'common.status.pending',
    RUNNING: 'common.status.running',
    DONE: 'common.status.done',
    FAILED: 'common.status.failed',
    CANCELLED: 'common.status.cancelled',
} as const satisfies Record<Job['status'], string>;

const isKnownJobStatus = (status: string): status is keyof typeof JOB_STATUS_KEYS =>
    Object.hasOwn(JOB_STATUS_KEYS, status);

export const getJobStatusLabel = (status: Job['status'], t: TranslateFn): string =>
    t(isKnownJobStatus(status) ? JOB_STATUS_KEYS[status] : 'common.labels.unknown');

export const isInvalidJob = (error: unknown): boolean => {
    if (isObject(error) && 'detail' in error) {
        const detail = String(error.detail);
        return detail.includes('Job not found') || detail.includes('Invalid job_id');
    }

    return false;
};

export const isJobDone = (job?: Job): boolean => job?.status === 'DONE';
export const isJobFailed = (job?: Job): boolean => job?.status === 'FAILED';
export const isJobRunning = (job?: Job): boolean => job?.status === 'RUNNING';
export const isJobPending = (job?: Job): boolean => job?.status === 'PENDING';

export const isTrainJob = (job?: Job): job is TrainJob => job?.job_type === 'train';
export const isQuantizeJob = (job?: Job): job is QuantizeJob => job?.job_type === 'quantize';
