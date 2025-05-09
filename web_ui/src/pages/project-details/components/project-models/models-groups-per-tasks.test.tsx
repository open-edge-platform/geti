// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved, within } from '@testing-library/react';

import { useGetRunningJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { ModelGroupsAlgorithmDetails } from '../../../../core/models/models.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { PerformanceType } from '../../../../core/projects/task.interface';
import { getMockedSupportedAlgorithm } from '../../../../core/supported-algorithms/services/test-utils';
import { TaskWithSupportedAlgorithms } from '../../../../core/supported-algorithms/supported-algorithms.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import {
    getMockedModelsGroupAlgorithmDetails,
    getMockedModelVersion,
} from '../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../providers/project-provider/project-provider.component';
import { useIsTraining } from './hooks/use-is-training.hook';
import { ModelsGroupsPerTasks } from './models-groups-per-tasks.component';

const tasks = [
    getMockedTask({ id: 'detection-id', domain: DOMAIN.DETECTION }),
    getMockedTask({ id: 'segmentation-id', domain: DOMAIN.SEGMENTATION }),
];
const mockedModelsGroups = [
    getMockedModelsGroupAlgorithmDetails({ taskId: tasks[0].id, groupId: 'yolo-v4-id', groupName: 'Yolo V4' }),
    getMockedModelsGroupAlgorithmDetails({ taskId: tasks[1].id, groupId: 'lite-x-id', groupName: 'Lite X' }),
];

const mockedSupportedAlgorithmsForDetection = [
    getMockedSupportedAlgorithm({
        name: 'YOLO',
        domain: DOMAIN.DETECTION,
        modelSize: 200,
        modelTemplateId: 'detection_yolo',
        gigaflops: 1.3,
        summary: 'YOLO architecture for detection',
    }),
    getMockedSupportedAlgorithm({
        name: 'SSD',
        domain: DOMAIN.DETECTION,
        modelSize: 100,
        modelTemplateId: 'detection_ssd',
        gigaflops: 5.4,
        summary: 'SSD architecture for detection',
    }),
    getMockedSupportedAlgorithm({
        name: 'ATTS',
        domain: DOMAIN.DETECTION,
        modelSize: 150,
        modelTemplateId: 'detection_atts',
        gigaflops: 3,
        isDefaultAlgorithm: true,
        summary: 'ATTS architecture for detection',
    }),
];

const mockedSupportedAlgorithmsForSegmentation = [
    getMockedSupportedAlgorithm({
        name: 'Lite-HRNet-18-mod2',
        domain: DOMAIN.SEGMENTATION,
        modelSize: 200,
        modelTemplateId: 'segmentation_Lite-HRNet-18-mod2',
        gigaflops: 1.3,
        summary: 'Lite-HRNet-18-mod2 architecture for segmentation',
    }),
    getMockedSupportedAlgorithm({
        name: 'Lite-HRNet-x-mod3',
        domain: DOMAIN.SEGMENTATION,
        modelSize: 100,
        modelTemplateId: 'segmentation_Lite-HRNet-x-mod3',
        gigaflops: 5.4,
        summary: 'Lite-HRNet-x-mod3 architecture for segmentation',
    }),
    getMockedSupportedAlgorithm({
        name: 'Lite-HRNet-s-mod2',
        domain: DOMAIN.SEGMENTATION,
        modelSize: 150,
        modelTemplateId: 'segmentation_Lite-HRNet-s-mod2',
        gigaflops: 3,
        isDefaultAlgorithm: true,
        summary: 'Lite-HRNet-s-mod2 architecture for segmentation',
    }),
];

const mockTasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms = {
    [tasks[0].id]: mockedSupportedAlgorithmsForDetection,
    [tasks[1].id]: mockedSupportedAlgorithmsForSegmentation,
};

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
        organizationId: 'organization-123',
    }),
}));

jest.mock('../../../../core/supported-algorithms/hooks/use-tasks-with-supported-algorithms', () => ({
    useTasksWithSupportedAlgorithms: jest.fn(() => ({
        tasksWithSupportedAlgorithms: mockTasksWithSupportedAlgorithms,
    })),
}));

jest.mock('./hooks/use-is-training.hook', () => ({
    useIsTraining: jest.fn(() => false),
}));

jest.mock('../../../../core/jobs/hooks/use-jobs.hook', () => ({
    useGetRunningJobs: jest.fn(() => ({ data: [] })),
}));

describe('ModelsGroupsPerTasks', () => {
    const renderModels = async (modelsGroups: ModelGroupsAlgorithmDetails[] = mockedModelsGroups) => {
        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <ModelsGroupsPerTasks modelsGroups={modelsGroups} tasks={tasks} />
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('Should render models groups per task', async () => {
        await renderModels();

        mockedModelsGroups.forEach((modelsGroup, idx) => {
            const group = screen.getByTestId(`${idMatchingFormat(tasks[idx].domain)}-id`);

            expect(screen.getByRole('heading', { name: new RegExp(tasks[idx].domain, 'i') })).toBeInTheDocument();
            expect(group).toBeInTheDocument();

            expect(within(group).getByText(modelsGroup.groupName, { exact: false })).toBeInTheDocument();
        });
    });

    it('Each models group should have its own training progress', async () => {
        const jobs = [
            getMockedJob({
                state: JobState.RUNNING,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId: tasks[0].id,
                        modelArchitecture: 'YoloV4',
                        name: 'Detection',
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
            }),
            getMockedJob({
                state: JobState.RUNNING,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId: tasks[1].id,
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
            }),
        ];

        jest.mocked(useIsTraining).mockReturnValue(true);
        jest.mocked(useGetRunningJobs).mockReturnValue({
            data: {
                // @ts-expect-error We don't care about mocking other fields
                pages: [{ jobs }],
            },
        });

        await renderModels();

        mockedModelsGroups.forEach((_modelsGroup, idx) => {
            expect(screen.getByTestId(`current-training-${tasks[idx].id}-id`)).toBeInTheDocument();
        });
    });

    it('Only first task should have training progress', async () => {
        const jobs = [
            getMockedJob({
                state: JobState.RUNNING,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId: tasks[0].id,
                        modelArchitecture: 'YoloV4',
                        name: 'Detection',
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
            }),
        ];

        jest.mocked(useIsTraining).mockReturnValue(true);
        jest.mocked(useGetRunningJobs).mockReturnValue({
            data: {
                // @ts-expect-error We don't care about mocking other fields
                pages: [{ jobs }],
            },
        });

        await renderModels();

        expect(screen.getByTestId(`current-training-${tasks[0].id}-id`)).toBeInTheDocument();
        expect(screen.queryByTestId(`current-training-${tasks[1].id}-id`)).not.toBeInTheDocument();
    });

    it('Only second task should have training progress', async () => {
        const jobs = [
            getMockedJob({
                state: JobState.RUNNING,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId: tasks[1].id,
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
            }),
        ];

        jest.mocked(useIsTraining).mockReturnValue(true);
        jest.mocked(useGetRunningJobs).mockReturnValue({
            data: {
                // @ts-expect-error We don't care about mocking other fields
                pages: [{ jobs }],
            },
        });

        await renderModels();

        expect(screen.getByTestId(`current-training-${tasks[1].id}-id`)).toBeInTheDocument();
        expect(screen.queryByTestId(`current-training-${tasks[0].id}-id`)).not.toBeInTheDocument();
    });

    it('Sorts models', async () => {
        const modelAA = getMockedModelVersion({
            performance: { score: 0.5, type: PerformanceType.DEFAULT },
            version: 1,
            id: 'model-aa-id',
        });
        const modelAB = getMockedModelVersion({
            performance: { score: 0.8, type: PerformanceType.DEFAULT },
            version: 2,
            id: 'model-ab-id',
        });
        const modelsGroupsA = getMockedModelsGroupAlgorithmDetails({
            taskId: tasks[0].id,
            groupId: 'yolo-v4-id',
            modelVersions: [modelAB, modelAA],
        });

        const modelBA = getMockedModelVersion({
            performance: { score: 0.2, type: PerformanceType.DEFAULT },
            version: 1,
            id: 'model-ba-id',
        });
        const modelBB = getMockedModelVersion({
            performance: { score: 0.9, type: PerformanceType.DEFAULT },
            version: 2,
            id: 'model-bb-id',
        });
        const modelsGroupsB = getMockedModelsGroupAlgorithmDetails({
            taskId: tasks[0].id,
            groupId: 'lite-x-id',
            modelVersions: [modelBB, modelBA],
        });

        await renderModels([modelsGroupsA, modelsGroupsB]);

        const expandModelsButtons = screen.getAllByRole('button', { name: /expand button/i });
        expandModelsButtons.forEach((button) => {
            fireEvent.click(button);
        });

        fireEvent.click(screen.getByRole('button', { name: /sort models/i }));
        const scoreAscending = screen.getAllByRole('menuitemradio', { name: 'Score' })[0];
        fireEvent.click(scoreAscending);

        const modelCardsAscendingScore = screen.getAllByTestId(/model-card/);

        expect(modelCardsAscendingScore).toEqual([
            screen.getByTestId(`model-card-${modelBA.id}`),
            screen.getByTestId(`model-card-${modelBB.id}`),
            screen.getByTestId(`model-card-${modelAA.id}`),
            screen.getByTestId(`model-card-${modelAB.id}`),
        ]);

        fireEvent.click(screen.getByRole('button', { name: /sort models/i }));
        const scoreDescending = screen.getAllByRole('menuitemradio', { name: 'Score' })[1];
        fireEvent.click(scoreDescending);

        const modelCardsDescendingScore = screen.getAllByTestId(/model-card/);

        expect(modelCardsDescendingScore).toEqual([
            screen.getByTestId(`model-card-${modelBB.id}`),
            screen.getByTestId(`model-card-${modelBA.id}`),
            screen.getByTestId(`model-card-${modelAB.id}`),
            screen.getByTestId(`model-card-${modelAA.id}`),
        ]);
    });
});
