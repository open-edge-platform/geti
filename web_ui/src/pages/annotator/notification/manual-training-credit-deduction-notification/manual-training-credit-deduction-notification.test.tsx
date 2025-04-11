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

import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { GETI_SYSTEM_AUTHOR_ID, JobState } from '../../../../core/jobs/jobs.const';
import { Job, JobCount } from '../../../../core/jobs/jobs.interface';
import { createInMemoryJobsService } from '../../../../core/jobs/services/in-memory-jobs-service';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { getMockedJob, getMockedJobCount } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { ManualTrainingCreditDeductionNotification } from './manual-training-credit-deduction-notification.component';

const mockedUseNotification = jest.fn();
jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: () => ({
        addNotification: mockedUseNotification,
    }),
}));

const mockedProjectIdentifier = {
    projectId: 'project-id',
    workspaceId: 'workspace-id',
    organizationId: 'organization-id',
};

describe('ManualTrainingCreditDeductionNotification', () => {
    const renderApp = async ({
        jobCount = {},
        isFlagOn = true,
        mockedJob = undefined,
    }: {
        isFlagOn?: boolean;
        jobCount?: Partial<JobCount>;
        mockedJob?: Job;
    }) => {
        const jobsService = createInMemoryJobsService();

        jobsService.getJobs = async () => ({
            jobs: [mockedJob ?? getMockedJob({ state: JobState.SCHEDULED })],
            jobsCount: getMockedJobCount(jobCount),
            nextPage: '',
        });

        providersRender(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <ManualTrainingCreditDeductionNotification />
            </ProjectProvider>,
            {
                services: { jobsService },
                featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: isFlagOn },
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('check that notification is opened only once and with right content', async () => {
        await renderApp({
            jobCount: { numberOfScheduledJobs: 1 },
        });

        await waitFor(() => {
            expect(mockedUseNotification).toHaveBeenNthCalledWith(1, {
                message: 'The model training has been started, 7 credits deducted.',
                type: NOTIFICATION_TYPE.INFO,
            });
        });
    });

    it('check that notification will not appear when number of scheduled jobs is 0', async () => {
        await renderApp({
            jobCount: { numberOfScheduledJobs: 0 },
        });

        expect(mockedUseNotification).not.toHaveBeenCalled();
    });

    it('check that notification will not appear if the scheduled job was triggered by autotraining', async () => {
        await renderApp({
            jobCount: { numberOfScheduledJobs: 0 },
            mockedJob: getMockedJob({ state: JobState.SCHEDULED, authorId: GETI_SYSTEM_AUTHOR_ID }),
        });

        expect(mockedUseNotification).not.toHaveBeenCalled();
    });

    it(`check that notification won't appear if credit system feature flag is disabled`, async () => {
        await renderApp({
            jobCount: { numberOfScheduledJobs: 1 },
            isFlagOn: false,
        });

        await waitFor(() => {
            expect(mockedUseNotification).not.toHaveBeenCalled();
        });
    });
});
