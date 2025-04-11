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

import { GETI_SYSTEM_AUTHOR_ID, JobState } from '../../../core/jobs/jobs.const';
import { JobCount } from '../../../core/jobs/jobs.interface';
import { getMockedJob, getMockedJobCount } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { JOB_TRIGGER, onScheduledTrainingJobs } from './utils';

const getJobResponse = (jobCount: Partial<JobCount> = {}) => ({
    pageParams: [undefined],
    pages: [
        {
            jobs: [getMockedJob({ state: JobState.SCHEDULED, authorId: GETI_SYSTEM_AUTHOR_ID })],
            nextPage: undefined,
            jobsCount: getMockedJobCount(jobCount),
        },
    ],
});

describe('credit-deduction-notification utils', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('onScheduledTrainingJobs', () => {
        const mockedCallback = jest.fn();

        it(`check that callback function is triggered requested job trigger does not match scheduled job's author`, () => {
            onScheduledTrainingJobs(mockedCallback, JOB_TRIGGER.AUTO)(getJobResponse({ numberOfScheduledJobs: 1 }));
            expect(mockedCallback).toBeCalledTimes(1);
        });

        it(`check that callback function is not triggered when requested job trigger does not match scheduled job's author`, () => {
            onScheduledTrainingJobs(mockedCallback, JOB_TRIGGER.MANUAL)(getJobResponse({ numberOfScheduledJobs: 1 }));
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('invalid response', () => {
            onScheduledTrainingJobs(mockedCallback, JOB_TRIGGER.AUTO)({ pageParams: [undefined], pages: [] });
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('non schedule jobs', () => {
            onScheduledTrainingJobs(mockedCallback, JOB_TRIGGER.AUTO)(getJobResponse());
            expect(mockedCallback).toBeCalledTimes(0);
        });
    });
});
