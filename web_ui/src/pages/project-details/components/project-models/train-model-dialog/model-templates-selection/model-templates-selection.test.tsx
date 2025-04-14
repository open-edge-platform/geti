// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { mockedArchitectureModels } from '../../../../../../core/models/services/test-utils';
import { DOMAIN } from '../../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../../core/projects/services/in-memory-project-service';
import { LifecycleStage } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { getMockedSupportedAlgorithm } from '../../../../../../core/supported-algorithms/services/test-utils';
import { TaskWithSupportedAlgorithms } from '../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../../../test-utils/project-provider-render';
import { ProjectProvider } from '../../../../providers/project-provider/project-provider.component';
import { getModelTemplates } from '../utils';
import { ModelTemplatesSelection } from './model-templates-selection.component';
import { ModelConfigurationOption } from './utils';

describe('ModelTemplatesSelection', () => {
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

    const mockedSupportedAlgorithmsForClassification = [
        getMockedSupportedAlgorithm({
            name: 'YOLO Classification',
            domain: DOMAIN.CLASSIFICATION,
            modelSize: 100,
            modelTemplateId: 'classification_yolo',
            gigaflops: 1.3,
            summary: 'YOLO architecture for classification',
        }),
        getMockedSupportedAlgorithm({
            name: 'SSD Classification',
            domain: DOMAIN.CLASSIFICATION,
            modelSize: 100,
            modelTemplateId: 'classification_ssd',
            gigaflops: 6.4,
            summary: 'SSD architecture for classification',
        }),
        getMockedSupportedAlgorithm({
            name: 'ATTS Classification',
            domain: DOMAIN.CLASSIFICATION,
            modelSize: 150,
            modelTemplateId: 'classification_atts',
            gigaflops: 3.2,
            summary: 'ATTS architecture for classification',
            isDefaultAlgorithm: true,
        }),
    ];

    const modelTemplates = getModelTemplates(mockedSupportedAlgorithmsForDetection);

    const selectedDetectionTask = getMockedTask({
        id: '1',
        domain: DOMAIN.DETECTION,
        labels: [],
        title: 'detection',
    });

    const selectedClassificationTask = getMockedTask({
        id: '2',
        domain: DOMAIN.CLASSIFICATION,
        labels: [],
        title: 'classification',
    });

    const tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms = {
        [selectedDetectionTask.id]: mockedSupportedAlgorithmsForDetection,
        [selectedClassificationTask.id]: mockedSupportedAlgorithmsForClassification,
    };

    const setSelectedTask = jest.fn();
    const handleSelectedTemplateId = jest.fn();
    const setModelConfigurationOption = jest.fn();
    const modelConfigurationOption = ModelConfigurationOption.LATEST_CONFIGURATION;

    const animationDirection = 1;

    const singleTaskProjectId = 'single-project-id';
    const taskChainProjectId = 'task-chain-project-id';
    const workspaceId = 'workspace-id';

    const projectService = createInMemoryProjectService();

    const mockedSingleTaskProject = getMockedProject({
        id: singleTaskProjectId,
        tasks: [{ id: selectedDetectionTask.id, domain: DOMAIN.DETECTION, labels: [], title: DOMAIN.DETECTION }],
        labels: [],
        datasets: [{ id: 'dataset-id', name: 'test dataset', creationTime: '', useForTraining: true }],
    });

    const mockedTaskChainProject = getMockedProject({
        id: taskChainProjectId,
        tasks: [
            { id: selectedDetectionTask.id, domain: DOMAIN.DETECTION, labels: [], title: DOMAIN.DETECTION },
            {
                id: selectedClassificationTask.id,
                domain: DOMAIN.CLASSIFICATION,
                labels: [],
                title: DOMAIN.CLASSIFICATION,
            },
        ],
        labels: [],
        datasets: [{ id: 'dataset-id', name: 'test dataset', creationTime: '', useForTraining: true }],
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('Picker with task selection should not be visible for single task project', async () => {
        projectService.getProject = jest.fn(async () => mockedSingleTaskProject);

        await render(
            <ModelTemplatesSelection
                modelConfigurationOption={modelConfigurationOption}
                setModelConfigurationOption={setModelConfigurationOption}
                tasksWithSupportedAlgorithms={tasksWithSupportedAlgorithms}
                selectedModelTemplateId={modelTemplates[0].modelTemplateId}
                handleSelectedTemplateId={handleSelectedTemplateId}
                selectedTask={selectedDetectionTask}
                setSelectedTask={setSelectedTask}
                animationDirection={animationDirection}
                models={mockedArchitectureModels}
            />,
            { services: { projectService } }
        );

        expect(screen.queryByRole('listbox', { name: 'Task', hidden: true })).not.toBeInTheDocument();
    });

    it('Picker with task selection should be visible for task chain project', async () => {
        projectService.getProject = jest.fn(async () => mockedTaskChainProject);
        await render(
            <ProjectProvider
                projectIdentifier={getMockedProjectIdentifier({ workspaceId, projectId: taskChainProjectId })}
            >
                <ModelTemplatesSelection
                    modelConfigurationOption={modelConfigurationOption}
                    setModelConfigurationOption={setModelConfigurationOption}
                    tasksWithSupportedAlgorithms={tasksWithSupportedAlgorithms}
                    selectedModelTemplateId={modelTemplates[0].modelTemplateId}
                    handleSelectedTemplateId={handleSelectedTemplateId}
                    selectedTask={selectedDetectionTask}
                    setSelectedTask={setSelectedTask}
                    animationDirection={animationDirection}
                    models={mockedArchitectureModels}
                />
            </ProjectProvider>,
            { services: { projectService } }
        );

        fireEvent.click(screen.getByRole('button', { name: 'Detection Select domain Task' }));

        expect(await screen.findByRole('listbox', { name: /Task/i })).toBeInTheDocument();
    });

    it('Model template should change when the selected task has changed', async () => {
        projectService.getProject = jest.fn(async () => mockedTaskChainProject);

        await render(
            <ModelTemplatesSelection
                modelConfigurationOption={modelConfigurationOption}
                setModelConfigurationOption={setModelConfigurationOption}
                tasksWithSupportedAlgorithms={tasksWithSupportedAlgorithms}
                selectedModelTemplateId={modelTemplates[0].modelTemplateId}
                handleSelectedTemplateId={handleSelectedTemplateId}
                selectedTask={selectedDetectionTask}
                setSelectedTask={setSelectedTask}
                animationDirection={animationDirection}
                models={mockedArchitectureModels}
            />,
            { services: { projectService } }
        );

        fireEvent.click(screen.getByRole('button', { name: 'Detection Select domain Task' }));

        const listbox = await screen.findByRole('listbox', { name: /Task/i });

        await userEvent.selectOptions(listbox, screen.getByRole('option', { name: /Classification/ }));

        expect(setSelectedTask).toHaveBeenCalled();
        expect(handleSelectedTemplateId).toHaveBeenCalled();
    });

    it('Model template selection should only show non-obsolete models', async () => {
        projectService.getProject = jest.fn(async () => mockedTaskChainProject);

        const mockTasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms = {
            [selectedDetectionTask.id]: [
                getMockedSupportedAlgorithm({
                    name: 'YOLO',
                    domain: DOMAIN.DETECTION,
                    modelSize: 200,
                    modelTemplateId: 'detection_yolo',
                    gigaflops: 1.3,
                    lifecycleStage: LifecycleStage.OBSOLETE,
                    summary: 'YOLO architecture for detection',
                }),
                getMockedSupportedAlgorithm({
                    name: 'SSD',
                    domain: DOMAIN.DETECTION,
                    modelSize: 100,
                    modelTemplateId: 'detection_ssd',
                    gigaflops: 5.4,
                    lifecycleStage: LifecycleStage.DEPRECATED,
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
            ],
            [selectedClassificationTask.id]: mockedSupportedAlgorithmsForClassification,
        };

        await render(
            <ModelTemplatesSelection
                modelConfigurationOption={modelConfigurationOption}
                setModelConfigurationOption={setModelConfigurationOption}
                tasksWithSupportedAlgorithms={mockTasksWithSupportedAlgorithms}
                selectedModelTemplateId={modelTemplates[0].modelTemplateId}
                handleSelectedTemplateId={handleSelectedTemplateId}
                selectedTask={selectedDetectionTask}
                setSelectedTask={setSelectedTask}
                animationDirection={animationDirection}
                models={mockedArchitectureModels}
            />,
            { services: { projectService } }
        );

        expect(screen.queryByText('YOLO')).not.toBeInTheDocument();
        expect(screen.queryByText('SSD')).toBeInTheDocument();
        expect(screen.getByText('ATTS')).toBeInTheDocument();
    });
});
