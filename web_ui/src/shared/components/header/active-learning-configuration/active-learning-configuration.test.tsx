// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { UseQueryResult } from '@tanstack/react-query';
import { fireEvent, screen } from '@testing-library/react';
import { AxiosError } from 'axios';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../core/projects/services/project-service.interface';
import { Task } from '../../../../core/projects/task.interface';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import {
    BooleanGroupParams,
    ConfigurableParametersTaskChain,
} from '../../configurable-parameters/configurable-parameters.interface';
import { ActiveLearningConfiguration, CornerIndicator } from './active-learning-configuration.component';

const mockedUseGetConfigParameters = jest.fn();
jest.mock('../../../../core/configurable-parameters/hooks/use-config-parameters.hook', () => ({
    useConfigParameters: jest.fn(() => ({
        useGetConfigParameters: mockedUseGetConfigParameters,
        reconfigureParametersMutation: { isLoading: true },
    })),
}));

const mockConfigParamData = ({
    tasks,
    autoTraining = true,
    dynamicRequiredAnnotations = true,
}: {
    tasks: Task[];
    autoTraining: boolean;
    dynamicRequiredAnnotations: boolean;
}) => {
    return {
        isLoading: false,
        data: tasks.map(({ id }) => ({
            taskId: id,
            components: [
                {
                    header: 'General',
                    parameters: [
                        {
                            header: 'Auto-training',
                            value: autoTraining,
                        },
                    ],
                },
                {
                    header: 'Annotation requirements',
                    parameters: [
                        {
                            header: 'Dynamic required annotations',
                            value: dynamicRequiredAnnotations,
                        },
                    ],
                },
            ],
        })),
    } as unknown as UseQueryResult<ConfigurableParametersTaskChain[], AxiosError>;
};

const renderApp = async (isDarkMode = true, selectedTask: Task | null = null, projectService: ProjectService) => {
    return render(<ActiveLearningConfiguration isDarkMode={isDarkMode} selectedTask={selectedTask} />, {
        services: { projectService },
    });
};

describe('ActiveLearningConfiguration', () => {
    const projectService = createInMemoryProjectService();

    const project = getMockedProject({
        tasks: [
            getMockedTask({ title: 'detection', id: 'detection', domain: DOMAIN.DETECTION }),
            getMockedTask({ title: 'classification', id: 'classification', domain: DOMAIN.CLASSIFICATION }),
        ],
    });
    projectService.getProject = async () => project;

    beforeEach(() => {
        jest.mocked(mockedUseGetConfigParameters).mockReturnValue(
            mockConfigParamData({ tasks: project.tasks, autoTraining: true, dynamicRequiredAnnotations: true })
        );
    });

    it('renders training settings tabs for each task', async () => {
        await renderApp(false, null, projectService);

        fireEvent.click(screen.getByRole('button', { name: 'Active learning configuration' }));

        expect(await screen.findByRole('heading', { name: 'Training' })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Select a task to configure its training settings/ }));

        for (const task of project.tasks) {
            expect(await screen.findByRole('option', { name: task.title })).toBeVisible();
        }
    });
});

describe('CornerIndicator Status', () => {
    const mockParams = (value: boolean | undefined) => ({
        task: getMockedTask({}),
        trainingConfig: { value } as BooleanGroupParams,
    });

    describe('Indicator Off', () => {
        it('trainingConfig is undefined', async () => {
            await render(<CornerIndicator autoTrainingTasks={[mockParams(undefined)]} />);

            expect(screen.getByLabelText(/Active learning configuration off/i)).toBeVisible();
        });
        it('multiple tasks', async () => {
            await render(<CornerIndicator autoTrainingTasks={[mockParams(false), mockParams(false)]} />);

            expect(screen.getByLabelText(/Active learning configuration off/i)).toBeVisible();
        });
    });

    describe('Indicator On', () => {
        it('trainingConfig is true', async () => {
            await render(<CornerIndicator autoTrainingTasks={[mockParams(true)]} />);

            expect(screen.getByLabelText(/Active learning configuration on/i)).toBeVisible();
        });
        it('multiple tasks', async () => {
            await render(<CornerIndicator autoTrainingTasks={[mockParams(true), mockParams(true)]} />);

            expect(screen.getByLabelText(/Active learning configuration on/i)).toBeVisible();
        });
    });

    describe('Indicator Split', () => {
        it('trainingConfig true and false', async () => {
            await render(<CornerIndicator autoTrainingTasks={[mockParams(true), mockParams(false)]} />);

            expect(screen.getByLabelText(/Active learning configuration split/i)).toBeVisible();
        });

        it('trainingConfig true and undefined', async () => {
            await render(<CornerIndicator autoTrainingTasks={[mockParams(true), mockParams(undefined)]} />);

            expect(screen.getByLabelText(/Active learning configuration split/i)).toBeVisible();
        });

        it('trainingConfig false and undefined', async () => {
            await render(<CornerIndicator autoTrainingTasks={[mockParams(true), mockParams(undefined)]} />);

            expect(screen.getByLabelText(/Active learning configuration split/i)).toBeVisible();
        });
    });
});
