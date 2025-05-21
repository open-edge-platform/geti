// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { mockedRunningTrainingJobs } from '../../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { TrainingProgress } from './training-progress.component';
import { useTrainingProgress } from './use-training-progress/use-training-progress.hook';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-1',
        organizationId: 'organization-123',
    }),
}));

jest.mock('./use-training-progress/use-training-progress.hook', () => ({
    useTrainingProgress: jest.fn(() => ({})),
}));

describe('Training progress', () => {
    const projectIdentifier = getMockedProjectIdentifier();

    it('Should display correct information about training progress', async () => {
        const trainingDetails = [mockedRunningTrainingJobs[0]];
        const archName = trainingDetails[0].metadata.task.modelArchitecture as string;

        jest.mocked(useTrainingProgress).mockImplementation(() => ({
            showTrainingProgress: true,
            trainingDetails,
        }));

        render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <TrainingProgress taskId={'task-id'} />
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.getByText('Test step (1 of 1)')).toBeInTheDocument();
        expect(screen.getByTestId('job-scheduler-job-1-progress')).toBeInTheDocument();
        expect(screen.getByText(archName)).toBeInTheDocument();
    });
});
