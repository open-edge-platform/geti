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
jest.mock('../../../../../../hooks/use-project-identifier/use-project-identifier', () => {
    return {
        useProjectIdentifier: jest.fn(() => {
            return {
                workspaceId: 'workspace-id',
                projectId: 'project-id',
            };
        }),
    };
});
jest.mock('../../../../../../core/supported-algorithms/hooks/use-tasks-with-supported-algorithms', () => ({
    ...jest.requireActual('../../../../../../core/supported-algorithms/hooks/use-tasks-with-supported-algorithms'),
    useTasksWithSupportedAlgorithms: () => ({
        tasksWithSupportedAlgorithms: {
            '321': [
                {
                    domain: 'Classification',
                    summary: 'Class-Incremental Image Classification for EfficientNet-B0',
                    gigaflops: 0.81,
                    isDefaultAlgorithm: true,
                    modelSize: 4.09,
                    name: 'EfficientNet-B0',
                    modelTemplateId: 'Custom_Image_Classification_EfficinetNet-B0',
                },
            ],
        },
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

    // eslint-disable-next-line max-len
    it('should display increased model version from the previously trained model, creation time, loading model info and inform that score is not available', async () => {
        const formattedCreationDate = formatDate(dayjs().toString(), 'DD MMM YYYY, hh:mm A');
        const mockedJob = getMockedJob({
            state: JobState.RUNNING,
            type: JobType.TRAIN,
            creationTime: formattedCreationDate,
            metadata: {
                task: {
                    taskId: 'segmentation-id',
                    modelArchitecture: 'SSD',
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

    // eslint-disable-next-line max-len
    it('should display model version 1 if there were not previously trained model in that architecture, creation time, loading model info and inform that score is not available', async () => {
        const formattedCreationDate = formatDate(dayjs().toString(), 'DD MMM YYYY, hh:mm A');
        const mockedJob = getMockedJob({
            state: JobState.RUNNING,
            type: JobType.TRAIN,
            creationTime: formattedCreationDate,
            metadata: {
                task: {
                    taskId: 'segmentation-id',
                    modelArchitecture: 'SSD',
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
        await render({ job: mockedJob, modelGroup: [] });

        expect(screen.getByTestId(`version-${mockedGenericId}-id`)).toHaveTextContent(`Version 1`);

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
