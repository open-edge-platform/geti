// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { createInMemoryJobsService } from '../../../../core/jobs/services/in-memory-jobs-service';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { FUX_NOTIFICATION_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedUserGlobalSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { JobsActionIcon } from './jobs-action-icon.component';

const fakeJobsService = createInMemoryJobsService();
const mockSaveConfig = jest.fn();
const mockSettings = getMockedUserGlobalSettingsObject({
    saveConfig: mockSaveConfig,
    isSavingConfig: false,
});

jest.mock('../../../../core/user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../../../core/user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(() => mockSettings),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

describe('jobs action icon', (): void => {
    beforeAll(() => {
        fakeJobsService.getJobs = jest.fn(
            (): Promise<JobsResponse> =>
                Promise.resolve({
                    jobs: [getMockedJob()],
                    jobsCount: {
                        numberOfRunningJobs: 1,
                        numberOfFinishedJobs: 0,
                        numberOfScheduledJobs: 0,
                        numberOfCancelledJobs: 0,
                        numberOfFailedJobs: 0,
                    },
                    nextPage: '',
                })
        );
    });

    const renderComponent = async (): Promise<void> => {
        providersRender(<JobsActionIcon />, { services: { jobsService: fakeJobsService } });
    };

    it('should show numbers of running jobs', async (): Promise<void> => {
        await renderComponent();

        expect(screen.getByText('bell.svg')).toBeInTheDocument();
        expect(await screen.findByTestId('number-badge-running-jobs-icon-value')).toHaveTextContent('1');
    });

    it('on click event should trigger dialog open and call save settings config', async (): Promise<void> => {
        await renderComponent();

        expect(screen.queryByRole('dialog')).toBeNull();

        fireEvent.click(screen.getByRole('button'));
        expect(screen.getByRole('dialog')).toBeVisible();
        expect(mockSaveConfig).toHaveBeenCalledWith({
            ...mockSettings.config,
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: false },
        });
    });
});
