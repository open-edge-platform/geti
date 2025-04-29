// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { createInMemoryJobsService } from '../../../core/jobs/services/in-memory-jobs-service';
import { JobsResponse } from '../../../core/jobs/services/jobs-service.interface';
import { MediaUploadProvider } from '../../../providers/media-upload-provider/media-upload-provider.component';
import { getMockedJob } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { projectRender } from '../../../test-utils/project-provider-render';
import { LandingPageHeader as Header } from './header.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({ organizationId: 'organization-id' })),
}));

const fakeJobsService = createInMemoryJobsService();

const render = async (isDarkMode = true) => {
    return await projectRender(
        <MediaUploadProvider>
            <Header isDarkMode={isDarkMode} isProject />
        </MediaUploadProvider>,
        { services: { jobsService: fakeJobsService } }
    );
};

describe('landing page header', () => {
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

    it('Check application title', async () => {
        await render();

        expect(await screen.findByLabelText('intel geti')).toBeInTheDocument();
    });

    it("Check header's color mode - grayscale", async () => {
        await render();

        const header = screen.getByTestId('application-header');

        expect(header).toHaveClass('gray200color');
        expect(header).not.toHaveClass('energyBlueShade1Color');
    });

    it("Check header's color mode - blue color", async () => {
        await render(false);

        const header = screen.getByTestId('application-header');

        expect(header).not.toHaveClass('gray200color');
        expect(header).toHaveClass('energyBlueShade1Color');
    });
});

describe('Jobs management', () => {
    beforeAll(() => {
        fakeJobsService.getJobs = async () =>
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
            });
    });

    it('Check if popover is properly open', async () => {
        await render();

        const button = screen.getByRole('button', { name: 'Jobs in progress' });
        expect(button).toBeInTheDocument();

        fireEvent.click(button);

        expect(await screen.findAllByRole('tab')).toHaveLength(5);
    });

    // Discussed with UX: Currently color of the badge is the same (red) in the whole app
    it('Check if jobs management icon is properly displayed', async () => {
        await render();

        expect(await screen.findByLabelText('intel geti')).toBeInTheDocument();

        const badge = await screen.findByTestId('number badge');
        expect(badge).toHaveClass('accented', { exact: false });
    });
});
