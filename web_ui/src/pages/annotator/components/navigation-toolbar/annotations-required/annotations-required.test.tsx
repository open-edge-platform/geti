// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, within } from '@testing-library/react';

import { BooleanGroupParams } from '../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { ProjectStatusTaskDTO } from '../../../../../core/projects/dtos/status.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { PerformanceType, Task } from '../../../../../core/projects/task.interface';
import { useActiveLearningConfiguration } from '../../../../../shared/components/header/active-learning-configuration/use-active-learning-configuration.hook';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import { AnnotationsRequired } from './annotations-required.component';

jest.mock(
    '../../../../../shared/components/header/active-learning-configuration/use-active-learning-configuration.hook',
    () => ({
        useActiveLearningConfiguration: jest.fn(() => ({ autoTrainingTasks: [] })),
    })
);

describe('Required annotations', () => {
    const fakeTaskOne = {
        id: 'task-1',
        title: 'Detection',
        labels: [getMockedLabel({ id: 'task-one-label' })],
        domain: DOMAIN.DETECTION,
        n_new_annotations: 2,
        required_annotations: {
            details: [],
            value: 64,
        },
    };
    const fakeTaskTwo = {
        id: 'task-2',
        title: 'Segmentation',
        labels: [getMockedLabel({ id: 'task-two-label' })],
        domain: DOMAIN.SEGMENTATION,
        n_new_annotations: 4,
        required_annotations: {
            details: [],
            value: 2,
        },
    };

    const renderApp = async (
        selectedTask: Task | null,
        tasksConfig: { task: Task; isTraining: boolean; isAutoTrainingOn: boolean }[]
    ) => {
        const domains = tasksConfig.map(({ task }) => task.domain);

        jest.mocked(useActiveLearningConfiguration).mockReturnValue({
            autoTrainingTasks: tasksConfig.map(({ task, isAutoTrainingOn }) => ({
                task,
                trainingConfig: { value: isAutoTrainingOn } as BooleanGroupParams,
            })),
            isPending: false,
            updateAutoTraining: jest.fn(),
            updateDynamicRequiredAnnotations: jest.fn(),
            updateRequiredImagesAutoTraining: jest.fn(),
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () =>
            getMockedProject({
                domains,
                name: 'test-project',
                tasks: tasksConfig.map(({ task }) => task),
            });

        projectService.getProjectStatus = async () => ({
            isTraining: false,
            performance: {
                type: PerformanceType.DEFAULT,
                score: 0.1,
                taskPerformances: [
                    {
                        score: {
                            value: 0.1,
                            metricType: 'accuracy',
                        },
                        taskNodeId: 'task-id',
                    },
                ],
            },
            tasks: tasksConfig.map(({ task, isTraining }) => ({
                ...task,
                is_training: isTraining,
            })) as unknown as ProjectStatusTaskDTO[],
        });

        await render(<AnnotationsRequired id={'test-id'} selectedTask={selectedTask} />, {
            services: { projectService },
        });
    };

    it('Displays the correct required annotations for single task project', async () => {
        await renderApp(fakeTaskOne, [{ task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true }]);

        const annotationsValue = screen.getByTestId('required-annotations-value');
        expect(within(annotationsValue).queryByText('Annotations required:')).toBeVisible();
        expect(await within(annotationsValue).findByText(fakeTaskOne.required_annotations.value)).toBeVisible();
    });

    it('Displays "new annotations" for single task project', async () => {
        await renderApp(fakeTaskOne, [{ task: fakeTaskOne, isTraining: false, isAutoTrainingOn: false }]);

        const annotationsValue = screen.getByTestId('required-annotations-value');
        expect(within(annotationsValue).queryByText('New annotations:')).toBeVisible();
        expect(within(annotationsValue).queryByText('Annotations required:')).not.toBeInTheDocument();
        expect(await within(annotationsValue).findByText(fakeTaskOne.n_new_annotations)).toBeVisible();
    });

    it('Displays the correct required annotations on task chain project with "All tasks" isAutoTrainingOn "true"', async () => {
        await renderApp(null, [
            { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true },
            { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: true },
        ]);
        const totalAnnotations = fakeTaskOne.required_annotations.value + fakeTaskTwo.required_annotations.value;

        const annotationsValue = screen.getByTestId('required-annotations-value');
        expect(within(annotationsValue).queryByText('Annotations required:')).toBeVisible();
        expect(await within(annotationsValue).findByText(`${totalAnnotations}`)).toBeVisible();
    });

    it('Displays the correct required annotations on task chain project with "All tasks" isAutoTrainingOn "false"', async () => {
        await renderApp(null, [
            { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: false },
            { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: false },
        ]);

        const totalAnnotations = fakeTaskOne.n_new_annotations + fakeTaskTwo.n_new_annotations;

        const annotationsValue = screen.getByTestId('required-annotations-value');
        expect(within(annotationsValue).queryByText('New annotations:')).toBeVisible();
        expect(await within(annotationsValue).findByText(`${totalAnnotations}`)).toBeVisible();
    });

    it('Displays the correct required annotations on task chain project with one of the tasks selected', async () => {
        await renderApp(fakeTaskTwo, [
            { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true },
            { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: true },
        ]);

        const annotationsValue = screen.getByTestId('required-annotations-value');
        expect(within(annotationsValue).queryByText('Annotations required:')).toBeVisible();
        expect(await within(annotationsValue).findByText(`${fakeTaskTwo.required_annotations.value}`)).toBeVisible();
    });

    it('Displays the correct training information on task chain project with one of the tasks selected training', async () => {
        await renderApp(fakeTaskTwo, [
            { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true },
            { task: fakeTaskTwo, isTraining: true, isAutoTrainingOn: true },
        ]);

        expect(await screen.findByTestId('training-dots')).toBeVisible();
        expect(screen.queryByTestId('required-annotations-value')).not.toBeInTheDocument();
    });

    it('Displays new annotations when one task has auto training on and second has auto training off', async () => {
        await renderApp(null, [
            { task: fakeTaskOne, isTraining: false, isAutoTrainingOn: true },
            { task: fakeTaskTwo, isTraining: false, isAutoTrainingOn: false },
        ]);

        const totalAnnotations = fakeTaskOne.n_new_annotations + fakeTaskTwo.n_new_annotations;

        const annotationsValue = screen.getByTestId('required-annotations-value');
        expect(within(annotationsValue).queryByText('New annotations:')).toBeVisible();
        expect(await within(annotationsValue).findByText(`${totalAnnotations}`)).toBeVisible();
    });
});
