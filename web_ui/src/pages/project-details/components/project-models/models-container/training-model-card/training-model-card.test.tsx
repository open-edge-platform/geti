// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import dayjs from 'dayjs';

import { JobState, JobType } from '../../../../../../core/jobs/jobs.const';
import { RunningTrainingJob } from '../../../../../../core/jobs/jobs.interface';
import { ModelsGroups } from '../../../../../../core/models/models.interface';
import { createInMemoryModelsService } from '../../../../../../core/models/services/in-memory-models-service';
import { formatDate } from '../../../../../../shared/utils';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedJob } from '../../../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedModelGroups } from '../../../../../../test-utils/mocked-items-factory/mocked-model';
import { providersRender } from '../../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../../providers/project-provider/project-provider.component';
import { TrainingModelCard } from './training-model-card.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
        organizationId: 'organization-id',
    }),
}));

describe('TrainingModelCard', () => {
    const render = async ({ job, modelGroup }: { job: RunningTrainingJob; modelGroup: ModelsGroups[] }) => {
        const modelsService = createInMemoryModelsService();
        modelsService.getModels = jest.fn(async () => modelGroup);

        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <TrainingModelCard job={job} />
            </ProjectProvider>,
            {
                services: {
                    modelsService,
                },
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('should display increased model version from the previously trained model, creation time, loading model info and inform that score is not available', async () => {
        const formattedCreationDate = formatDate(dayjs().toString(), 'DD MMM YYYY, hh:mm A');

        const mockedJob = getMockedJob({
            state: JobState.RUNNING,
            type: JobType.TRAIN,
            creationTime: formattedCreationDate,
            metadata: {
                task: {
                    taskId: 'segmentation-id',
                    modelArchitecture: 'YoloV4',
                    name: 'Segmentation',
                    datasetStorageId: 'dataset-storage-id',
                    modelTemplateId: 'template-id',
                },
                project: {
                    id: '123',
                    name: 'example project',
                },
                trainedModel: {
                    modelId: 'model-id',
                },
            },
        }) as RunningTrainingJob;
        const mockedGenericId = `training-model-${mockedJob.metadata.trainedModel.modelId}`;
        const mockedModelGroup = [getMockedModelGroups()];
        await render({ job: mockedJob, modelGroup: mockedModelGroup });

        expect(screen.getByTestId(`version-${mockedGenericId}-id`)).toHaveTextContent(
            `Version ${mockedModelGroup[0].modelVersions[0].version + 1}`
        );

        expect(screen.getByText(`Score not available`)).toBeInTheDocument();
        expect(screen.getByTestId('trained-model-date-id')).toHaveTextContent(`Trained: ${formattedCreationDate}`);

        await waitFor(() => {
            const container = screen.getByTestId(`model-info-${mockedGenericId}-id`);

            expect(container).toHaveTextContent('Model weight size');
            expect(container).toHaveTextContent('Total size');
            expect(container).toHaveTextContent('Complexity');
        });
    });
});
