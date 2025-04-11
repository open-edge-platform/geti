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
import { UserGlobalSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getMockedJob, getMockedJobCount } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import {
    getMockedUserGlobalSettings,
    getMockedUserGlobalSettingsObject,
} from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { useIsAutoTrainingOn } from '../../hooks/use-is-auto-training-on.hook';
import { CreditDeductionNotification } from './credit-deduction-notification.component';

const mockedUseNotification = jest.fn();
jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: () => ({
        addNotification: mockedUseNotification,
    }),
}));

jest.mock('../../hooks/use-is-auto-training-on.hook', () => ({
    ...jest.requireActual('../../hooks/use-is-auto-training-on.hook'),
    useIsAutoTrainingOn: jest.fn(),
}));

const mockedProjectIdentifier = {
    projectId: 'project-id',
    workspaceId: 'workspace-id',
    organizationId: 'organization-id',
};

describe('CreditDeductionNotification', () => {
    const renderApp = async ({
        jobCount = {},
        settings = {},
        isFlagOn = true,
        isAutoTrainingOn = true,
        mockedScheduledJob = undefined,
    }: {
        isFlagOn?: boolean;
        isAutoTrainingOn?: boolean;
        jobCount?: Partial<JobCount>;
        settings?: Partial<UserGlobalSettings>;
        mockedScheduledJob?: Job;
    }) => {
        const jobsService = createInMemoryJobsService();

        jobsService.getJobs = async () => ({
            jobs: [
                mockedScheduledJob ??
                    getMockedJob({
                        state: JobState.SCHEDULED,
                        cost: { requests: [{ amount: 10, unit: 'images' }], leaseId: '123', consumed: [] },
                    }),
            ],
            jobsCount: getMockedJobCount(jobCount),
            nextPage: '',
        });

        jest.mocked(useIsAutoTrainingOn).mockReturnValue(isAutoTrainingOn);

        providersRender(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <CreditDeductionNotification
                    settings={getMockedUserGlobalSettingsObject({ config: getMockedUserGlobalSettings(settings) })}
                />
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

    describe('auto-training is on, credit system feature flag is enabled', () => {
        it('check that when scheduled jobs number is 0 the notification will not appear', async () => {
            await renderApp({
                jobCount: { numberOfScheduledJobs: 0 },
                settings: {
                    autoTrainingCreditModal: { isEnabled: false },
                    autoTrainingCreditNotification: { isEnabled: false },
                },
            });

            expect(mockedUseNotification).not.toHaveBeenCalled();
        });

        it('check that when credit modal enabled the notification will not appear', async () => {
            await renderApp({
                jobCount: { numberOfScheduledJobs: 1 },
                settings: {
                    autoTrainingCreditModal: { isEnabled: true },
                    autoTrainingCreditNotification: { isEnabled: false },
                },
            });

            expect(mockedUseNotification).not.toHaveBeenCalled();
        });

        it('check that when credit modal if off and credit notification is enabled this notification will not appear', async () => {
            await renderApp({
                jobCount: { numberOfScheduledJobs: 1 },
                settings: {
                    autoTrainingCreditModal: { isEnabled: false },
                    autoTrainingCreditNotification: { isEnabled: true },
                },
            });

            await waitFor(() => {
                expect(mockedUseNotification).not.toHaveBeenCalled();
            });
        });

        it('check that when both credit modal and notification are disabled, but scheduled job was triggered manually the notification will not appear', async () => {
            await renderApp({
                jobCount: { numberOfScheduledJobs: 1 },
                settings: {
                    autoTrainingCreditModal: { isEnabled: false },
                    autoTrainingCreditNotification: { isEnabled: false },
                },
            });

            await waitFor(() => {
                expect(mockedUseNotification).toHaveBeenCalledTimes(0);
            });
        });

        it('check that when both credit modal and notification are disabled and the scheduled job was triggered by autotraining the notification will appear once', async () => {
            await renderApp({
                jobCount: { numberOfScheduledJobs: 1 },
                settings: {
                    autoTrainingCreditModal: { isEnabled: false },
                    autoTrainingCreditNotification: { isEnabled: false },
                },
                mockedScheduledJob: getMockedJob({
                    state: JobState.SCHEDULED,
                    authorId: GETI_SYSTEM_AUTHOR_ID,
                    cost: { requests: [{ amount: 10, unit: 'images' }], leaseId: '123', consumed: [] },
                }),
            });

            await waitFor(() => {
                expect(mockedUseNotification).toHaveBeenCalledTimes(1);
            });
        });
    });
});
