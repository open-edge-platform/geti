// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { CreateApiModelConfigParametersService } from '../../../../core/configurable-parameters/services/api-model-config-parameters-service';
import { createInMemoryApiModelConfigParametersService } from '../../../../core/configurable-parameters/services/in-memory-api-model-config-parameters-service';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../core/projects/services/project-service.interface';
import { Task } from '../../../../core/projects/task.interface';
import { getMockedProjectConfiguration } from '../../../../test-utils/mocked-items-factory/mocked-configuration-parameters';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { ActiveLearningConfiguration, CornerIndicator } from './active-learning-configuration.component';

const renderApp = async ({
    isDarkMode = true,
    selectedTask = null,
    projectService,
    configParametersService = createInMemoryApiModelConfigParametersService(),
    FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS,
}: {
    isDarkMode: boolean;
    selectedTask: Task | null;
    projectService: ProjectService;
    configParametersService?: CreateApiModelConfigParametersService;
    FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: boolean;
}) => {
    await render(<ActiveLearningConfiguration isDarkMode={isDarkMode} selectedTask={selectedTask} />, {
        services: { projectService, configParametersService },
        featureFlags: { FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS },
    });

    await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Active learning configuration' })).toBeEnabled();
    });
};

describe('ActiveLearningConfiguration', () => {
    describe('with FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS disabled', () => {
        const projectService = createInMemoryProjectService();
        const configParametersService = createInMemoryApiModelConfigParametersService();

        const project = getMockedProject({
            tasks: [
                getMockedTask({ title: 'detection', id: 'detection', domain: DOMAIN.DETECTION }),
                getMockedTask({ title: 'classification', id: 'classification', domain: DOMAIN.CLASSIFICATION }),
            ],
        });

        // @ts-expect-error We don't need to mock all the parameter's fields
        configParametersService.getConfigParameters = async () => {
            return Promise.resolve(
                project.tasks.map(({ id }) => ({
                    taskId: id,
                    components: [
                        {
                            header: 'General',
                            parameters: [
                                {
                                    header: 'Auto-training',
                                    value: true,
                                },
                            ],
                        },
                        {
                            header: 'Annotation requirements',
                            parameters: [
                                {
                                    header: 'Dynamic required annotations',
                                    value: true,
                                },
                            ],
                        },
                    ],
                }))
            );
        };

        projectService.getProject = async () => project;

        it('renders training settings tabs for each task', async () => {
            await renderApp({
                isDarkMode: false,
                selectedTask: null,
                projectService,
                configParametersService,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
            });

            fireEvent.click(screen.getByRole('button', { name: 'Active learning configuration' }));

            expect(await screen.findByRole('heading', { name: 'Training' })).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /Select a task to configure its training settings/ }));

            for (const task of project.tasks) {
                expect(await screen.findByRole('option', { name: task.title })).toBeVisible();
            }
        });
    });

    describe('with FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS enabled', () => {
        const projectService = createInMemoryProjectService();
        const configParametersService = createInMemoryApiModelConfigParametersService();

        const project = getMockedProject({
            tasks: [
                getMockedTask({ title: 'detection', id: 'detection', domain: DOMAIN.DETECTION }),
                getMockedTask({ title: 'classification', id: 'classification', domain: DOMAIN.CLASSIFICATION }),
            ],
        });

        configParametersService.getProjectConfiguration = async () => {
            const projectConfiguration = getMockedProjectConfiguration();

            return Promise.resolve(
                getMockedProjectConfiguration({
                    taskConfigs: [
                        {
                            taskId: project.tasks[0].id,
                            training: { constraints: [] },
                            autoTraining: projectConfiguration.taskConfigs[0].autoTraining,
                        },
                        {
                            taskId: project.tasks[1].id,
                            training: { constraints: [] },
                            autoTraining: projectConfiguration.taskConfigs[0].autoTraining,
                        },
                    ],
                })
            );
        };

        projectService.getProject = async () => project;

        it('renders training settings tabs for each task', async () => {
            await renderApp({
                isDarkMode: false,
                selectedTask: null,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: true,
                projectService,
                configParametersService,
            });

            fireEvent.click(screen.getByRole('button', { name: 'Active learning configuration' }));

            await waitForElementToBeRemoved(screen.getByRole('progressbar', { name: 'Loading' }));

            screen.debug();

            expect(await screen.findByRole('heading', { name: 'Training' })).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /Select a task to configure its training settings/ }));

            for (const task of project.tasks) {
                expect(await screen.findByRole('option', { name: task.title })).toBeVisible();
            }
        });
    });
});

describe('CornerIndicator Status', () => {
    describe('Indicator Off', () => {
        it('trainingConfig is false', async () => {
            await render(<CornerIndicator allAutoTrainingValues={[false]} />);

            expect(screen.getByLabelText(/Active learning configuration off/i)).toBeVisible();
        });
        it('multiple tasks', async () => {
            await render(<CornerIndicator allAutoTrainingValues={[false, false]} />);

            expect(screen.getByLabelText(/Active learning configuration off/i)).toBeVisible();
        });
    });

    describe('Indicator On', () => {
        it('trainingConfig is true', async () => {
            await render(<CornerIndicator allAutoTrainingValues={[true]} />);

            expect(screen.getByLabelText(/Active learning configuration on/i)).toBeVisible();
        });
        it('multiple tasks', async () => {
            await render(<CornerIndicator allAutoTrainingValues={[true, true]} />);

            expect(screen.getByLabelText(/Active learning configuration on/i)).toBeVisible();
        });
    });

    describe('Indicator Split', () => {
        it('trainingConfig true and false', async () => {
            await render(<CornerIndicator allAutoTrainingValues={[true, false]} />);

            expect(screen.getByLabelText(/Active learning configuration split/i)).toBeVisible();
        });
    });
});
