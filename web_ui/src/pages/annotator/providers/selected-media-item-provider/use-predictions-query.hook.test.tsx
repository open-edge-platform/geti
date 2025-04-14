// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';

import { createInMemoryInferenceService } from '../../../../core/annotations/services/in-memory-inference-service';
import { PredictionCache, PredictionMode } from '../../../../core/annotations/services/prediction-service.interface';
import { Label } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { TaskProvider } from '../task-provider/task-provider.component';
import { usePredictionsQuery } from './use-predictions-query.hook';

const mediaItem = getMockedImageMediaItem({});
const datasetIdentifier = {
    workspaceId: 'workspace-id',
    projectId: 'project-id',
    datasetId: 'dataset-id',
    organizationId: 'organization-id',
};

const wrapper = ({ children }: { children?: ReactNode }) => {
    return (
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier(datasetIdentifier)}>
            <TaskProvider>{children}</TaskProvider>
        </ProjectProvider>
    );
};

describe('usePredictionsQuery', (): void => {
    beforeEach(() => {
        jest.resetAllMocks();
    });

    const taskId = '123';
    const coreLabels: Label[] = [];
    const predictionArguments = { taskId, coreLabels, mediaItem, datasetIdentifier };

    const mockedInferenceService = createInMemoryInferenceService();
    const initialProps = { inferenceService: mockedInferenceService };

    beforeEach(() => {
        mockedInferenceService.getPredictions = jest.fn();
        mockedInferenceService.getExplanations = jest.fn();
    });

    it('task-chain projects call the service with taskId ', async (): Promise<void> => {
        const mockedProjectService = createInMemoryProjectService();

        mockedProjectService.getProject = async () =>
            getMockedProject({
                tasks: [getMockedTask({ domain: DOMAIN.DETECTION }), getMockedTask({ domain: DOMAIN.CLASSIFICATION })],
            });

        const { result } = renderHookWithProviders(
            () => usePredictionsQuery({ ...predictionArguments, predictionId: PredictionMode.ONLINE }),
            { wrapper, providerProps: { ...initialProps, projectService: mockedProjectService } }
        );

        await waitFor(() => {
            expect(result.current).toBeDefined();
        });

        expect(mockedInferenceService.getExplanations).toHaveBeenCalledWith(
            datasetIdentifier,
            mediaItem,
            taskId,
            undefined,

            // AbortController
            expect.anything()
        );
        expect(mockedInferenceService.getPredictions).toHaveBeenCalledWith(
            datasetIdentifier,
            coreLabels,
            mediaItem,
            PredictionCache.NEVER,
            taskId,
            undefined,
            // AbortController
            expect.anything()
        );
    });

    it('use PredictionCache.AUTO by default', async (): Promise<void> => {
        renderHookWithProviders(() => usePredictionsQuery(predictionArguments), {
            wrapper,
            providerProps: { ...initialProps },
        });

        await waitFor(() => {
            expect(mockedInferenceService.getExplanations).not.toHaveBeenCalled();
            expect(mockedInferenceService.getPredictions).toHaveBeenCalledWith(
                datasetIdentifier,
                coreLabels,
                mediaItem,
                PredictionCache.AUTO,
                undefined,
                undefined,
                // AbortController
                expect.anything()
            );
        });
    });

    it('PredictionMode LATEST is handle as PredictionCache.ALWAYS', async (): Promise<void> => {
        const onSuccess = jest.fn();

        renderHookWithProviders(
            () => usePredictionsQuery({ ...predictionArguments, onSuccess, predictionId: PredictionMode.LATEST }),
            {
                wrapper,
                providerProps: { ...initialProps },
            }
        );

        await waitFor(() => {
            expect(onSuccess).toHaveBeenCalled();
        });

        expect(mockedInferenceService.getExplanations).not.toHaveBeenCalled();
        expect(mockedInferenceService.getPredictions).toHaveBeenCalledWith(
            datasetIdentifier,
            coreLabels,
            mediaItem,
            PredictionCache.ALWAYS,
            undefined,
            undefined,
            // AbortController
            expect.anything()
        );
    });

    it('PredictionMode.ONLINE is sent as PredictionCache.NEVER, getExplanations is called', async (): Promise<void> => {
        renderHookWithProviders(
            () => usePredictionsQuery({ ...predictionArguments, predictionId: PredictionMode.ONLINE }),
            {
                wrapper,
                providerProps: { ...initialProps },
            }
        );

        await waitFor(() => {
            expect(mockedInferenceService.getExplanations).toHaveBeenCalledWith(
                datasetIdentifier,
                mediaItem,
                undefined,
                undefined,
                // AbortController
                expect.anything()
            );
        });

        expect(mockedInferenceService.getPredictions).toHaveBeenCalledWith(
            datasetIdentifier,
            coreLabels,
            mediaItem,
            PredictionCache.NEVER,
            undefined,
            undefined,
            // AbortController
            expect.anything()
        );
    });

    it('does not call "getExplanations" for keypoint detection projects', async (): Promise<void> => {
        const mockedProjectService = createInMemoryProjectService();

        mockedProjectService.getProject = async () =>
            getMockedProject({ tasks: [getMockedTask({ domain: DOMAIN.KEYPOINT_DETECTION })] });

        renderHookWithProviders(
            () => usePredictionsQuery({ ...predictionArguments, predictionId: PredictionMode.ONLINE }),
            {
                wrapper,
                providerProps: { ...initialProps, projectService: mockedProjectService },
            }
        );

        await waitFor(() => {
            expect(mockedInferenceService.getPredictions).toHaveBeenCalled();
        });

        expect(mockedInferenceService.getExplanations).not.toHaveBeenCalled();
    });
});
