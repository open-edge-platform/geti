// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { act, screen } from '@testing-library/react';
import { getMockedTrainJob } from 'mocks/mock-job';
import { render } from 'test-utils/render';

import { RunningJobRow } from './running-job-row.component';

describe('RunningJobRow', () => {
    beforeEach(() => {
        rs.useFakeTimers();
        rs.setSystemTime(new Date('2026-01-01T00:00:05Z'));
    });

    afterEach(() => {
        rs.useRealTimers();
    });

    it('updates elapsed time while the job status stays the same', () => {
        const job = getMockedTrainJob({ status: 'RUNNING', started_at: '2026-01-01T00:00:00Z', finished_at: null });

        render(<RunningJobRow job={job} showStatusBadge={false} architectureName={'Model'} onViewLogs={rs.fn()} />);

        expect(screen.getByText(/Elapsed 5s/)).toBeInTheDocument();

        act(() => {
            rs.advanceTimersByTime(1_000);
        });

        expect(screen.getByText(/Elapsed 6s/)).toBeInTheDocument();
    });
});
