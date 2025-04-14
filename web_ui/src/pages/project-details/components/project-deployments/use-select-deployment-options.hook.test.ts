// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, renderHook } from '@testing-library/react';

import { Task } from '../../../../core/projects/task.interface';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { DeployModelByTask } from './interfaces';
import { useSelectDeploymentOptions } from './use-select-deployment-options.hook';

describe('useSelectDeploymentOptions', () => {
    const mockTasks: Task[] = [getMockedTask({ id: 'first-task' }), getMockedTask({ id: 'second-task' })];

    it('should return NextButton enabled and download button disabled by default', () => {
        const mockModelSelection: DeployModelByTask = {
            [mockTasks[0].id]: {
                modelGroupId: 'model-group-id',
                modelId: 'model-id',
                optimisationId: 'optimization-id',
                versionId: 'version-id',
            },
            [mockTasks[1].id]: {
                modelGroupId: 'model-group-id-2',
                modelId: 'model-id-2',
                optimisationId: undefined,
                versionId: 'version-id-2',
            },
        };

        const { result } = renderHook(() =>
            useSelectDeploymentOptions({ tasks: mockTasks, modelSelection: mockModelSelection })
        );

        expect(result.current.nextButtonEnabled).toBeTruthy();
        expect(result.current.downloadEnabled).toBeFalsy();
    });

    it('should disable the next button if there is not optimization model selected', () => {
        const mockModelSelection: DeployModelByTask = {
            [mockTasks[0].id]: {
                modelGroupId: 'model-group-id',
                modelId: 'model-id',
                optimisationId: undefined,
                versionId: 'version-id',
            },
            [mockTasks[1].id]: {
                modelGroupId: 'model-group-id-2',
                modelId: 'model-id-2',
                optimisationId: 'optimization-id-2',
                versionId: 'version-id-2',
            },
        };

        const { result } = renderHook(() =>
            useSelectDeploymentOptions({ tasks: mockTasks, modelSelection: mockModelSelection })
        );

        expect(result.current.nextButtonEnabled).toBeFalsy();
    });

    it('should enable downloadButton if all tasks have models fully selected', () => {
        const mockModelSelection: DeployModelByTask = {
            [mockTasks[0].id]: {
                modelGroupId: 'model-group-id',
                modelId: 'model-id',
                optimisationId: 'optimization-id',
                versionId: 'version-id',
            },
            [mockTasks[1].id]: {
                modelGroupId: 'model-group-id-2',
                modelId: 'model-id-2',
                optimisationId: 'optimization-id-2',
                versionId: 'version-id-2',
            },
        };

        const {
            result: { current },
        } = renderHook(() => useSelectDeploymentOptions({ tasks: mockTasks, modelSelection: mockModelSelection }));

        expect(current.downloadEnabled).toBeTruthy();
    });

    it('should correctly update state when changing to next or previous task', async () => {
        const mockModelSelection: DeployModelByTask = {
            [mockTasks[0].id]: {
                modelGroupId: 'model-group-id',
                modelId: 'model-id',
                optimisationId: 'optimization-id',
                versionId: 'version-id',
            },
            [mockTasks[1].id]: {
                modelGroupId: 'model-group-id-2',
                modelId: 'model-id-2',
                optimisationId: 'optimization-id-2',
                versionId: 'version-id-2',
            },
        };

        const { result } = renderHook(() =>
            useSelectDeploymentOptions({ tasks: mockTasks, modelSelection: mockModelSelection })
        );

        // Select next task
        act(result.current.next);

        expect(result.current.prevButtonEnabled).toBeTruthy();
        expect(result.current.taskIndex).toEqual(1);
        expect(result.current.selectedTask).toEqual(mockTasks[1]);
        expect(result.current.showNextButton).toBeFalsy();
    });

    it('should showNextButton only if it is not the last task', async () => {
        const mockModelSelection: DeployModelByTask = {
            [mockTasks[0].id]: {
                modelGroupId: 'model-group-id',
                modelId: 'model-id',
                optimisationId: 'optimization-id',
                versionId: 'version-id',
            },
            [mockTasks[1].id]: {
                modelGroupId: 'model-group-id-2',
                modelId: 'model-id-2',
                optimisationId: 'optimization-id-2',
                versionId: 'version-id-2',
            },
        };

        const { result } = renderHook(() =>
            useSelectDeploymentOptions({ tasks: mockTasks, modelSelection: mockModelSelection })
        );

        expect(result.current.showNextButton).toBeTruthy();

        // Select the next task (which is the last one)
        act(result.current.next);

        expect(result.current.showNextButton).toBeFalsy();
    });

    it('should show prev button only if it is not the first task', async () => {
        const mockModelSelection: DeployModelByTask = {
            [mockTasks[0].id]: {
                modelGroupId: 'model-group-id',
                modelId: 'model-id',
                optimisationId: 'optimization-id',
                versionId: 'version-id',
            },
            [mockTasks[1].id]: {
                modelGroupId: 'model-group-id-2',
                modelId: 'model-id-2',
                optimisationId: 'optimization-id-2',
                versionId: 'version-id-2',
            },
        };

        const { result } = renderHook(() =>
            useSelectDeploymentOptions({ tasks: mockTasks, modelSelection: mockModelSelection })
        );

        expect(result.current.prevButtonEnabled).toBeFalsy();

        // Select the next task (which is the last one)
        act(() => {
            result.current.next();
        });

        expect(result.current.prevButtonEnabled).toBeTruthy();
    });
});
