// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor } from '@testing-library/react';
import { TransformComponent } from 'react-zoom-pan-pinch';

import { JobType } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { createInMemoryJobsService } from '../../../../core/jobs/services/in-memory-jobs-service';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedJob, getMockedJobStep } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { CustomRenderOptions } from '../../../../test-utils/required-providers-render';
import { getById } from '../../../../test-utils/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { annotatorRender as render } from '../../test-utils/annotator-render';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { Footer } from './footer.component';

jest.mock('../../../../shared/utils', () => ({
    ...jest.requireActual('../../../../shared/utils'),
    trimText: jest.fn((text) => text),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        selectedTask: null,
        activeDomains: [],
        tasks: [],
        isTaskChainDomainSelected: () => false,
    })),
}));

const trainingJob: Job = {
    ...getMockedJob({
        type: JobType.TRAIN,
        steps: [getMockedJobStep({ message: 'Training - Base model training', progress: 63 })],
    }),
};
const classificationJob: Job = {
    ...getMockedJob({
        type: JobType.IMPORT_PROJECT,
        metadata: {
            // @ts-expect-error we only care about the taskId
            task: {
                taskId: '1234',
            },
        },
        steps: [getMockedJobStep({ message: 'Training - Classification model training', progress: 80 })],
    }),
};

const renderFooter = async (options?: CustomRenderOptions) => {
    return render(
        <ZoomProvider>
            <TransformComponent>
                <Footer />
            </TransformComponent>
        </ZoomProvider>,
        options
    );
};

describe('Annotator Footer', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('Displays training progress correctly if there is no training', async () => {
        const { container } = await renderFooter();

        await waitFor(() => {
            expect(getById(container, 'training-progress')).toBeInTheDocument();
        });

        expect(screen.getByText('Waiting for user annotations')).toBeInTheDocument();
    });

    it('Displays training progress correctly if there is general training', async () => {
        const jobsService = createInMemoryJobsService();
        jobsService.getJobs = async () => {
            return {
                jobs: [trainingJob],
                jobsCount: {
                    numberOfCancelledJobs: 0,
                    numberOfFailedJobs: 0,
                    numberOfFinishedJobs: 0,
                    numberOfRunningJobs: 1,
                    numberOfScheduledJobs: 0,
                },
                nextPage: undefined,
            };
        };

        const { container } = await renderFooter({ services: { jobsService } });

        await waitFor(() => {
            expect(getById(container, 'training-progress')).toBeInTheDocument();
        });

        expect(await screen.findByText('Training - Base model training')).toBeInTheDocument();
        expect(screen.getByTestId('training-progress-percentage')).toHaveTextContent('63%');
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('Displays training progress for a specific task', async () => {
        const fakeTask = { id: '1234', title: 'Classification', labels: [], domain: DOMAIN.CLASSIFICATION };

        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: [fakeTask],
            selectedTask: fakeTask,
            activeDomains: [],
            isTaskChainDomainSelected: () => false,
        }));

        const jobsService = createInMemoryJobsService();
        jobsService.getJobs = async () =>
            Promise.resolve({
                jobs: [trainingJob, classificationJob],
                jobsCount: {
                    numberOfCancelledJobs: 0,
                    numberOfFailedJobs: 0,
                    numberOfFinishedJobs: 0,
                    numberOfRunningJobs: 2,
                    numberOfScheduledJobs: 0,
                },
                nextPage: undefined,
            });

        const { container } = await renderFooter({ services: { jobsService } });

        await waitFor(() => {
            expect(getById(container, 'training-progress')).toBeInTheDocument();
        });

        await waitFor(() => {
            expect(screen.getByText('Training - Classification model training')).toBeInTheDocument();
            expect(screen.getByTestId('training-progress-percentage')).toHaveTextContent('80%');
            expect(screen.getByRole('progressbar')).toBeInTheDocument();
        });
    });
});
