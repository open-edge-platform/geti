// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen, waitFor } from '@testing-library/react';

import { createInMemoryJobsService } from '../../../../core/jobs/services/in-memory-jobs-service';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { usePWA } from '../../../../hooks/use-pwa/use-pwa.hook';
import { MediaUploadProvider } from '../../../../providers/media-upload-provider/media-upload-provider.component';
import { ProgressiveWebAppProvider } from '../../../../providers/progressive-web-app-provider/progressive-web-app-provider.component';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { projectRender } from '../../../../test-utils/project-provider-render';
import { getById } from '../../../../test-utils/utils';
import { HeaderActions } from './header-actions.component';

jest.mock('../../../../hooks/use-pwa/use-pwa.hook', () => ({
    usePWA: jest.fn(() => ({
        isPWAReady: false,
    })),
}));

jest.mock('../../../../hooks/use-organization-identifier/use-organization-identifier.hook', () => ({
    useOrganizationIdentifier: jest.fn(() => ({
        organizationId: 'organization-id',
    })),
}));

const fakeJobsService = createInMemoryJobsService();

const render = async ({ isDarkMode = true, isProject = true, isAnomalyProject = false, isCreditSystemOn = false }) => {
    return projectRender(
        <ProgressiveWebAppProvider>
            <MediaUploadProvider>
                <HeaderActions isDarkMode={isDarkMode} isProject={isProject} isAnomalyProject={isAnomalyProject} />
            </MediaUploadProvider>
        </ProgressiveWebAppProvider>,
        { featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: isCreditSystemOn }, services: { jobsService: fakeJobsService } }
    );
};

describe('Header actions', () => {
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

    it('Check if grayscale has proper class', async () => {
        const { container } = await render({});

        const headerActionsContainer = getById(container, 'header-actions-container');

        await waitFor(() => {
            expect(headerActionsContainer).toBeInTheDocument();
        });

        expect(headerActionsContainer).not.toHaveClass('basicColor');
    });

    it('Check if proper class is set when grayscale is false', async () => {
        const { container } = await render({ isDarkMode: false });

        const headerActionsContainer = getById(container, 'header-actions-container');

        await waitFor(() => {
            expect(headerActionsContainer).toBeInTheDocument();
        });

        expect(headerActionsContainer).toHaveClass('basicColor');
    });

    it('Should show an additional install-pwa option if the app is PwaReady', async () => {
        jest.mocked(usePWA).mockImplementation(() => ({
            isPWAReady: true,
            handlePromptInstallApp: jest.fn(),
        }));

        await render({});

        await waitFor(() => expect(screen.getAllByRole('button')).toHaveLength(6));

        const options = screen.getAllByRole('button');

        expect(options[0]).toBe(screen.getByLabelText('Install Geti (PWA)'));
        expect(options).toHaveLength(6);
    });

    it('Check if there are proper actions and in proper order', async () => {
        jest.mocked(usePWA).mockImplementation(() => ({
            isPWAReady: false,
            handlePromptInstallApp: jest.fn(),
        }));

        await render({});

        expect(await screen.findByLabelText('User actions')).toBeInTheDocument();
        expect(screen.getByLabelText('Active learning configuration')).toBeInTheDocument();
        expect(screen.getByLabelText('Jobs in progress')).toBeInTheDocument();
        expect(screen.getByLabelText('Documentation actions')).toBeInTheDocument();
        expect(screen.getAllByRole('button')).toHaveLength(5);
    });

    it('Check if there is number of running jobs shown', async () => {
        await render({ isDarkMode: false });

        expect(await screen.findByTestId('number-badge-running-jobs-icon-value')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
    });

    describe('Check Auto training', () => {
        it('hidden with anomaly projects', async () => {
            await render({ isDarkMode: true, isProject: true, isAnomalyProject: true });

            expect(screen.queryByRole('button', { name: 'Active learning configuration' })).not.toBeInTheDocument();
        });

        it('hidden with project "false"', async () => {
            await render({ isDarkMode: true, isProject: false });

            expect(screen.queryByRole('button', { name: 'Active learning configuration' })).not.toBeInTheDocument();
        });
    });

    it('credit balance status is visible', async () => {
        await render({ isDarkMode: true, isCreditSystemOn: true });

        expect(screen.queryByRole('button', { name: 'credit balance status' })).toBeVisible();
    });
});
