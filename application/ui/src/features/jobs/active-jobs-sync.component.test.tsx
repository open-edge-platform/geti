// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';
import { vi } from 'vitest';

import { getMockedTrainJob } from '../../../mocks/mock-job';
import { http } from '../../api/utils';
import { server } from '../../msw-node-setup';
import { MockEventSourceConstructor, resetMockEventSource } from '../../test-utils/mock-event-source';
import { ActiveJobsSync } from './active-jobs-sync.component';

describe('ActiveJobsSync', () => {
    beforeEach(() => {
        resetMockEventSource();
    });

    it('opens an SSE stream for every active train/quantize job and none for terminal ones', async () => {
        const runningJob = getMockedTrainJob({ job_id: 'running-job', status: 'RUNNING' });
        const doneJob = getMockedTrainJob({ job_id: 'done-job', status: 'DONE' });
        server.use(http.get('/api/jobs', () => HttpResponse.json([runningJob, doneJob])));

        render(<ActiveJobsSync />);

        await waitFor(() => {
            expect(MockEventSourceConstructor).toHaveBeenCalledTimes(1);
            expect(MockEventSourceConstructor).toHaveBeenCalledWith(expect.stringContaining(runningJob.job_id));
        });
    });

    it('closes the stream once the job reaches a terminal status', async () => {
        const runningJob = getMockedTrainJob({ job_id: 'running-job', status: 'RUNNING' });
        server.use(http.get('/api/jobs', () => HttpResponse.json([runningJob])));

        render(<ActiveJobsSync />);

        await waitFor(() => expect(MockEventSourceConstructor).toHaveBeenCalledTimes(1));

        const eventSource = MockEventSourceConstructor.mock.results.at(-1)?.value;
        const closeSpy = vi.spyOn(eventSource, 'close');

        eventSource.onmessage?.({
            data: JSON.stringify({ ...runningJob, status: 'DONE' }),
        } as unknown as Event);

        await waitFor(() => expect(closeSpy).toHaveBeenCalled());
    });
});
