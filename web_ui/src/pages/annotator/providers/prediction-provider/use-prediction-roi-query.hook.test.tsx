// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { waitFor } from '@testing-library/react';

import { TaskChainInput } from '../../../../core/annotations/annotation.interface';
import { createInMemoryInferenceService } from '../../../../core/annotations/services/in-memory-inference-service';
import { InferenceService } from '../../../../core/annotations/services/inference-service.interface';
import { PredictionCache } from '../../../../core/annotations/services/prediction-service.interface';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { getMockedImage } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { DatasetProvider } from '../dataset-provider/dataset-provider.component';
import {
    SelectedMediaItemProps,
    useSelectedMediaItem,
} from '../selected-media-item-provider/selected-media-item-provider.component';
import { SelectedMediaItem } from '../selected-media-item-provider/selected-media-item.interface';
import { useTaskChain } from '../task-chain-provider/task-chain-provider.component';
import { TaskProvider } from '../task-provider/task-provider.component';
import { usePredictionsRoiQuery } from './use-prediction-roi-query.hook';

const selectedMediaItem = {
    ...getMockedImageMediaItem({}),
    image: getMockedImage(),
    annotations: [],
};

jest.mock('../selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

jest.mock('../task-chain-provider/task-chain-provider.component', () => ({
    ...jest.requireActual('../task-chain-provider/task-chain-provider.component'),
    useTaskChain: jest.fn(() => ({ inputs: [] })),
}));

jest.mock('../../hooks/use-annotator-mode', () => ({
    ...jest.requireActual('../../hooks/use-annotator-mode'),
    useAnnotatorMode: jest.fn(() => ({ isActiveLearningMode: true })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace_1',
        organizationId: 'organization-id',
    }),
}));

const mockedUseHasActiveModels = jest.fn();
jest.mock('../../../../core/models/hooks/use-models.hook', () => ({
    useModels: () => ({
        useHasActiveModels: mockedUseHasActiveModels,
    }),
}));

const mockUseSelectedMediaItem = (mediaItem?: SelectedMediaItem) =>
    jest.mocked(useSelectedMediaItem).mockImplementation(
        () =>
            ({
                selectedMediaItem: mediaItem,
            }) as unknown as SelectedMediaItemProps
    );

const mockUseTaskChain = (selectedInput: TaskChainInput[] = []) =>
    jest.mocked(useTaskChain).mockImplementation(() => ({
        inputs: selectedInput,
        outputs: [],
    }));

const mockedInferenceService = createInMemoryInferenceService();
mockedInferenceService.getPredictions = jest.fn();
mockedInferenceService.getExplanations = jest.fn();
mockedInferenceService.getInferenceServerStatus = async () => ({
    isInferenceServerReady: true,
});

describe('usePredictionsRoiQuery', () => {
    beforeEach(() => {
        jest.clearAllMocks();

        mockUseTaskChain();
        mockUseSelectedMediaItem(selectedMediaItem);
        mockedUseHasActiveModels.mockReturnValue({ hasActiveModels: true, isSuccess: true });

        jest.mocked(useAnnotatorMode).mockImplementation(() => ({
            isActiveLearningMode: true,
            currentMode: ANNOTATOR_MODE.ACTIVE_LEARNING,
        }));
    });

    const taskId = '213';
    const datasetIdentifier = {
        workspaceId: 'workspace_1',
        projectId: 'project-id',
        datasetId: 'in-memory-dataset',
        organizationId: 'organization-id',
    };

    const renderPredictionsRoiQuery = (params: {
        inferenceService: InferenceService;
        selectedInput: TaskChainInput;
        taskId: string;
    }) => {
        return renderHookWithProviders(
            () => usePredictionsRoiQuery({ taskId: params.taskId, selectedInput: params.selectedInput }),
            {
                wrapper: ({ children }) => (
                    <ProjectProvider projectIdentifier={datasetIdentifier}>
                        <TaskProvider>
                            <DatasetProvider>{children}</DatasetProvider>
                        </TaskProvider>
                    </ProjectProvider>
                ),
                providerProps: { inferenceService: params.inferenceService },
            }
        );
    };

    it('invalid selectedMediaItem', async () => {
        const selectedInput = getMockedAnnotation({ id: 'test-annotation-2', isSelected: true }) as TaskChainInput;
        mockUseSelectedMediaItem();

        const { result } = renderPredictionsRoiQuery({
            selectedInput,
            inferenceService: mockedInferenceService,
            taskId,
        });

        await waitFor(() => {
            expect(result.current.data).toEqual({ annotations: [], maps: [] });
        });
    });

    it('empty values predictions', async () => {
        const { result } = renderPredictionsRoiQuery({
            taskId,
            selectedInput: getMockedAnnotation({ id: undefined }) as TaskChainInput,
            inferenceService: mockedInferenceService,
        });

        await waitFor(() => {
            expect(result.current.data).toEqual({
                annotations: [],
                maps: [],
            });
        });

        expect(mockedInferenceService.getPredictions).not.toHaveBeenCalled();
    });

    const selectedInput = getMockedAnnotation({ id: 'test-annotation-2', isSelected: true }) as TaskChainInput;

    beforeEach(() => {
        mockUseTaskChain([selectedInput]);
    });

    it('calls inferenceService "getPredictions"', async () => {
        renderPredictionsRoiQuery({
            selectedInput,
            inferenceService: mockedInferenceService,
            taskId,
        });

        await waitFor(() => {
            expect(mockedInferenceService.getPredictions).toHaveBeenLastCalledWith(
                datasetIdentifier,
                expect.anything(),
                selectedMediaItem,
                PredictionCache.AUTO,
                taskId,
                selectedInput,
                // AbortController
                expect.anything()
            );
        });

        expect(mockedInferenceService.getExplanations).not.toHaveBeenCalled();
    });

    describe('PredictionMode.ONLINE is sent as PredictionCache.NEVER, calls "getPredictions" and "getExplanations"', () => {
        it('successful responses', async () => {
            jest.mocked(useAnnotatorMode).mockImplementation(() => ({
                isActiveLearningMode: false,
                currentMode: ANNOTATOR_MODE.PREDICTION,
            }));

            renderPredictionsRoiQuery({
                selectedInput,
                inferenceService: mockedInferenceService,
                taskId,
            });

            await waitFor(() => {
                expect(mockedInferenceService.getPredictions).toHaveBeenLastCalledWith(
                    datasetIdentifier,
                    expect.anything(),
                    selectedMediaItem,
                    PredictionCache.NEVER,
                    taskId,
                    selectedInput,
                    // AbortController
                    expect.anything()
                );
            });

            expect(mockedInferenceService.getExplanations).toHaveBeenLastCalledWith(
                datasetIdentifier,
                selectedMediaItem,
                taskId,
                selectedInput,
                // AbortController
                expect.anything()
            );
        });

        it('rejected requests are handle as empty', async () => {
            jest.mocked(useAnnotatorMode).mockImplementation(() => ({
                isActiveLearningMode: false,
                currentMode: ANNOTATOR_MODE.PREDICTION,
            }));
            jest.mocked(mockedInferenceService.getPredictions).mockRejectedValue('test error');
            jest.mocked(mockedInferenceService.getExplanations).mockRejectedValue('test error');

            const { result } = renderPredictionsRoiQuery({
                selectedInput,
                inferenceService: mockedInferenceService,
                taskId,
            });

            await waitFor(() => {
                expect(result.current.data).toEqual({ annotations: [], maps: [] });
            });
        });
    });
});
