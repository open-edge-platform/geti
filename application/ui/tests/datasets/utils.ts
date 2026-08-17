// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Job } from '@/api/types';
import { getMockedJob } from 'mocks/mock-job';
import { getMockedStagedDataset } from 'mocks/mock-staged-dataset';
import { HttpResponse } from 'msw';

import { http } from '../fixtures';

export const STAGED_DATASET_ID = 'staged-dataset-789';
export const PREPARE_JOB_ID = 'prepare-job-123';
export const IMPORT_JOB_ID = 'import-job-456';
export const DATASET_FILENAME = 'my-dataset.zip';

export const getMockedPrepareJob = (overrides: Partial<Job> = {}) =>
    getMockedJob({
        job_id: PREPARE_JOB_ID,
        job_type: 'prepare_dataset_for_import',
        status: 'RUNNING',
        progress: 50,
        message: 'Analyzing dataset archive...',
        ...overrides,
    });

export const getMockedImportJob = (
    jobType: 'import_dataset_as_new_project' | 'import_dataset_to_project',
    overrides: Partial<Job> = {}
) =>
    getMockedJob({
        job_id: IMPORT_JOB_ID,
        job_type: jobType,
        status: 'RUNNING',
        progress: 0,
        message: 'Importing dataset...',
        ...overrides,
    });

export const stagedDatasetWithMetadata = getMockedStagedDataset({
    id: STAGED_DATASET_ID,
    ready_for_import: true,
    metadata: {
        labels: ['cat', 'dog'],
        num_images: 100,
        num_annotated_images: 80,
        num_frames: 0,
        num_annotated_frames: 0,
        num_annotations: 200,
        annotation_type: 'bounding_box',
        num_videos: 0,
    },
});

const SSE_HEADERS = { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' };
const SNAPSHOT_STEP_MS = 1_000;

// Responses are buffered by @msw/playwright, so a connection can only carry one snapshot. Which
// snapshot is picked by elapsed time rather than connection count, so a client that reconnects or
// opens the stream twice still observes every step.
export const jobStatusStreamHandler = (snapshotsByJobId: Record<string, Job[]>) => {
    const firstRequestedAt = new Map<string, number>();

    return http.get('/api/jobs/{job_id}/status', ({ params }) => {
        const jobId = params.job_id as string;
        const snapshots = snapshotsByJobId[jobId] ?? [];

        if (snapshots.length === 0) {
            return new HttpResponse(':ok\n\n', { status: 200, headers: SSE_HEADERS });
        }

        const startedAt = firstRequestedAt.get(jobId) ?? Date.now();
        firstRequestedAt.set(jobId, startedAt);

        const step = Math.floor((Date.now() - startedAt) / SNAPSHOT_STEP_MS);
        const snapshot = snapshots[Math.min(step, snapshots.length - 1)];

        return new HttpResponse(`data: ${JSON.stringify(snapshot)}\n\n`, {
            status: 200,
            headers: SSE_HEADERS,
        });
    });
};

export const deleteStagedDatasetHandler = () => {
    let deletedId: string | undefined;

    const handler = http.delete('/api/staged_datasets/{staged_dataset_id}', ({ params }) => {
        deletedId = params.staged_dataset_id as string;
        return new HttpResponse(null, { status: 204 });
    });

    return { handler, getDeletedId: () => deletedId };
};
