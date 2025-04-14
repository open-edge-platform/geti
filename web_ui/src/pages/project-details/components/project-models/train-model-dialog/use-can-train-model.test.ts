// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import {
    getMockedProjectStatus,
    getMockedProjectStatusTask,
} from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../../test-utils/render-hook-with-providers';
import { useCanTrainModel } from './use-can-train-model.hook';

describe('useCanTrainModel', () => {
    const projectIdentifier = getMockedProjectIdentifier();
    const task = getMockedTask();

    it('returns true when the task is ready to train based on server response', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({
                    tasks: [getMockedProjectStatusTask({ id: task.id, ready_to_train: true })],
                })
            );

        const { result } = renderHookWithProviders(() => useCanTrainModel(projectIdentifier, task), {
            providerProps: {
                projectService,
            },
        });

        await waitFor(() => {
            expect(result.current).toEqual({ canTrainModel: true, numberOfRequiredAnnotations: undefined });
        });
    });

    it('returns true when the task is ready to train (and server sent outdated information -> big edge case)', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({
                    tasks: [getMockedProjectStatusTask({ id: task.id, ready_to_train: false, n_new_annotations: 3 })],
                })
            );

        const { result } = renderHookWithProviders(() => useCanTrainModel(projectIdentifier, task), {
            providerProps: {
                projectService,
            },
        });

        await waitFor(() => {
            expect(result.current).toEqual({ canTrainModel: true, numberOfRequiredAnnotations: undefined });
        });
    });

    it('returns false with the correct number of required annotations when the task is not ready to train', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({
                    tasks: [getMockedProjectStatusTask({ id: task.id, ready_to_train: false, n_new_annotations: 1 })],
                })
            );

        const { result } = renderHookWithProviders(() => useCanTrainModel(projectIdentifier, task), {
            providerProps: {
                projectService,
            },
        });

        await waitFor(() => {
            expect(result.current).toEqual({ canTrainModel: false, numberOfRequiredAnnotations: 2 });
        });
    });

    it('returns false with the correct number of required annotations when there are no new annotations', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({
                    tasks: [getMockedProjectStatusTask({ id: task.id, ready_to_train: false, n_new_annotations: 0 })],
                })
            );

        const { result } = renderHookWithProviders(() => useCanTrainModel(projectIdentifier, task), {
            providerProps: {
                projectService,
            },
        });

        await waitFor(() => {
            expect(result.current).toEqual({ canTrainModel: false, numberOfRequiredAnnotations: 3 });
        });
    });

    it('returns false with the correct number of required annotations when the task is not found', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({
                    tasks: [
                        getMockedProjectStatusTask({
                            id: task.id + 'yolo',
                            ready_to_train: false,
                            n_new_annotations: 0,
                        }),
                    ],
                })
            );

        const { result } = renderHookWithProviders(() => useCanTrainModel(projectIdentifier, task), {
            providerProps: {
                projectService,
            },
        });

        await waitFor(() => {
            expect(result.current).toEqual({ canTrainModel: false, numberOfRequiredAnnotations: 3 });
        });
    });
});
