// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useSearchParams } from 'react-router-dom';

import { MediaItem } from '../../../../core/media/media.interface';
import { ModelsGroups } from '../../../../core/models/models.interface';
import { hasActiveModels } from '../../../../core/models/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedModelsGroup, getMockedModelVersion } from '../../../../test-utils/mocked-items-factory/mocked-model';
import { mockedProjectContextProps } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender } from '../../../../test-utils/project-provider-render';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import {
    ExplanationOpacityContextProps,
    PredictionContextProps,
    useExplanationOpacity,
    usePrediction,
} from '../../providers/prediction-provider/prediction-provider.component';
import {
    SelectedMediaItemProps,
    useSelectedMediaItem,
} from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { AnnotationPredictionToggle } from './annotation-prediction-toggle.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useSearchParams: jest.fn(),
}));

jest.mock('../../providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../providers/prediction-provider/prediction-provider.component'),
    usePrediction: jest.fn(),
    useExplanationOpacity: jest.fn(),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({ isTaskChainProject: false })),
}));

jest.mock('../../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

const mockUseHasActiveModels = jest.fn();
jest.mock('../../../../core/models/hooks/use-models.hook', () => ({
    ...jest.requireActual('../../../../core/models/hooks/use-models.hook'),
    useModels: jest.fn(() => ({
        useHasActiveModels: mockUseHasActiveModels,
    })),
}));

jest.mock('../../hooks/use-annotator-mode', () => ({
    ...jest.requireActual('../../hooks/use-annotator-mode'),
    useAnnotatorMode: jest.fn(),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

const loadedModelData = [getMockedModelsGroup({ modelVersions: [getMockedModelVersion({ isActiveModel: true })] })];

describe('AnnotationPredictionToggle', () => {
    const getAnnotationButton = () => screen.getByRole('button', { name: 'Select annotation mode' });
    const getPredictionButton = () => screen.getByRole('button', { name: 'Select prediction mode' });

    const renderApp = async (
        {
            mode = ANNOTATOR_MODE.ACTIVE_LEARNING,
            modelData = [] as ModelsGroups[],
            mockPredictionsQuery = { refetch: jest.fn() },
            mockSelectedMediaItemQuery = { refetch: jest.fn() },
            mockedSetExplanationVisible = jest.fn(),
            mockedSetShowOverlapAnnotations = jest.fn(),
            mockedUseTask = mockedTaskContextProps({}),
            mockedPredictionsRoiQuery = { refetch: jest.fn() },
            FEATURE_FLAG_VISUAL_PROMPT_SERVICE = false,
        },
        selectedMediaItem: MediaItem | null = getMockedImageMediaItem({})
    ) => {
        mockUseHasActiveModels.mockReturnValue({ hasActiveModels: modelData.some(hasActiveModels), isSuccess: true });
        jest.mocked(useTask).mockReturnValue(mockedUseTask);

        jest.mocked(useSelectedMediaItem).mockReturnValue({
            predictionsQuery: mockPredictionsQuery,
            selectedMediaItemQuery: mockSelectedMediaItemQuery,
            selectedMediaItem: selectedMediaItem === null ? undefined : selectedMediaItem,
        } as unknown as SelectedMediaItemProps);

        jest.mocked(useAnnotatorMode).mockReturnValue({
            currentMode: mode,
            isActiveLearningMode: mode === ANNOTATOR_MODE.ACTIVE_LEARNING,
        });

        jest.mocked(useAnnotationToolContext).mockReturnValue(
            fakeAnnotationToolContext({
                mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
            })
        );

        jest.mocked(usePrediction).mockReturnValue({
            predictionsRoiQuery: mockedPredictionsRoiQuery,
            setExplanationVisible: mockedSetExplanationVisible,
        } as unknown as PredictionContextProps);

        jest.mocked(useExplanationOpacity).mockReturnValue({
            setShowOverlapAnnotations: mockedSetShowOverlapAnnotations,
        } as unknown as ExplanationOpacityContextProps);

        const searchParams = new URLSearchParams();
        const setSpy = jest.spyOn(searchParams, 'set');

        searchParams.set('mode', mode);
        setSpy.mockClear();

        const setSearchParams = jest.fn();

        jest.mocked(useSearchParams).mockImplementation(() => [searchParams, setSearchParams]);

        await projectRender(<AnnotationPredictionToggle />, {
            featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE },
        });

        return setSpy;
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('prediction is disabled while loading models', async () => {
        await renderApp({
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
        });

        expect(getAnnotationButton()).toBeEnabled();
        expect(getPredictionButton()).toBeDisabled();
    });

    it('prediction is disabled with empty models', async () => {
        await renderApp({
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
        });

        expect(getAnnotationButton()).toBeEnabled();
        expect(getPredictionButton()).toBeDisabled();
    });

    it('annotation is selected by default', async () => {
        await renderApp({
            mode: undefined,
        });

        expect(getAnnotationButton()).toBeEnabled();
        expect(getAnnotationButton()).toHaveAttribute('class', expect.stringContaining('is-selected'));
    });

    it('selects prediction mode', async () => {
        const mockedUseTask = mockedTaskContextProps({ activeDomains: [DOMAIN.SEGMENTATION] });

        const setSpy = await renderApp({
            mockedUseTask,
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
            modelData: loadedModelData,
        });

        fireEvent.click(getPredictionButton());

        expect(setSpy).toHaveBeenLastCalledWith('mode', ANNOTATOR_MODE.PREDICTION);
    });

    it('selects active-learning mode', async () => {
        const mockedUseTask = mockedTaskContextProps({ activeDomains: [DOMAIN.CLASSIFICATION] });

        const setSpy = await renderApp({
            mockedUseTask,
            mode: ANNOTATOR_MODE.PREDICTION,
            modelData: loadedModelData,
        });

        fireEvent.click(getAnnotationButton());

        expect(setSpy).toHaveBeenLastCalledWith('mode', ANNOTATOR_MODE.ACTIVE_LEARNING);
    });

    describe('initial prediction mode', () => {
        it('prediction is selected by default', async () => {
            await renderApp({
                mode: ANNOTATOR_MODE.PREDICTION,
                modelData: loadedModelData,
            });

            expect(getPredictionButton()).toBeEnabled();
            expect(getPredictionButton()).toHaveAttribute('class', expect.stringContaining('is-selected'));
        });

        it('prediction mode with empty models redirects to ACTIVE_LEARNING', async () => {
            const mockedUseTask = mockedTaskContextProps({ activeDomains: [DOMAIN.SEGMENTATION] });

            const setSpy = await renderApp({
                mockedUseTask,
                mode: ANNOTATOR_MODE.PREDICTION,
            });

            expect(getPredictionButton()).toBeDisabled();
            expect(setSpy).toHaveBeenLastCalledWith('mode', ANNOTATOR_MODE.ACTIVE_LEARNING);
        });

        it('prediction mode with empty models does not redirect to ACTIVE_LEARNING when using prompt inference', async () => {
            const mockedUseTask = mockedTaskContextProps({ activeDomains: [DOMAIN.SEGMENTATION] });

            const setSpy = await renderApp({
                mockedUseTask,
                mode: ANNOTATOR_MODE.PREDICTION,
                FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true,
            });

            expect(getPredictionButton()).toBeEnabled();
            expect(setSpy).not.toHaveBeenCalled();
        });

        it('selects annotation mode', async () => {
            const mockedSetExplanationVisible = jest.fn();
            const mockedSetShowOverlapAnnotations = jest.fn();
            const mockedUseTask = mockedTaskContextProps({ activeDomains: [DOMAIN.SEGMENTATION] });

            const setSpy = await renderApp({
                mode: ANNOTATOR_MODE.PREDICTION,
                modelData: loadedModelData,
                mockedUseTask,
                mockedSetExplanationVisible,
                mockedSetShowOverlapAnnotations,
            });

            fireEvent.click(getAnnotationButton());

            expect(setSpy).toHaveBeenLastCalledWith('mode', ANNOTATOR_MODE.ACTIVE_LEARNING);
            expect(mockedSetExplanationVisible).toHaveBeenNthCalledWith(1, false);
            expect(mockedSetShowOverlapAnnotations).toHaveBeenNthCalledWith(1, false);
        });

        it('selects current mode twice', async () => {
            const mockedSetExplanationVisible = jest.fn();
            const mockedSetShowOverlapAnnotations = jest.fn();

            const setSpy = await renderApp({
                mode: ANNOTATOR_MODE.PREDICTION,
                modelData: loadedModelData,
                mockedSetExplanationVisible,
                mockedSetShowOverlapAnnotations,
            });

            fireEvent.click(getPredictionButton());

            expect(setSpy).not.toHaveBeenCalled();
            expect(mockedSetExplanationVisible).not.toHaveBeenCalled();
            expect(mockedSetShowOverlapAnnotations).not.toHaveBeenCalled();
        });

        it('annotation is selected by default with empty models', async () => {
            const setSpy = await renderApp({
                mode: ANNOTATOR_MODE.PREDICTION,
            });

            expect(setSpy).toHaveBeenLastCalledWith('mode', ANNOTATOR_MODE.ACTIVE_LEARNING);
        });

        it('segmentation, selecting prediction mode refetch predictions', async () => {
            const mockPredictionsQuery = { refetch: jest.fn() };
            const mockedPredictionsRoiQuery = { refetch: jest.fn() };
            const mockSelectedMediaItemQuery = { refetch: jest.fn() };

            const setSearchParameters = await renderApp({
                mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
                modelData: loadedModelData,
                mockPredictionsQuery,
                mockedPredictionsRoiQuery,
                mockSelectedMediaItemQuery,
            });

            expect(getPredictionButton()).toBeEnabled();
            expect(setSearchParameters).not.toHaveBeenCalled();

            fireEvent.click(getPredictionButton());

            await waitFor(() => {
                expect(setSearchParameters).toHaveBeenCalledWith('mode', 'predictions');
                expect(mockedPredictionsRoiQuery.refetch).not.toHaveBeenCalled();
            });
        });

        it('segmentation, selecting prediction mode without a selected media item does not refetch predictions', async () => {
            const mockPredictionsQuery = { refetch: jest.fn() };
            const mockedPredictionsRoiQuery = { refetch: jest.fn() };
            const mockSelectedMediaItemQuery = { refetch: jest.fn() };

            await renderApp(
                {
                    mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
                    modelData: loadedModelData,
                    mockPredictionsQuery,
                    mockedPredictionsRoiQuery,
                    mockSelectedMediaItemQuery,
                },
                null
            );

            expect(getPredictionButton()).toBeEnabled();
            expect(mockPredictionsQuery.refetch).not.toHaveBeenCalled();

            fireEvent.click(getPredictionButton());

            expect(mockPredictionsQuery.refetch).not.toHaveBeenCalled();
            expect(mockSelectedMediaItemQuery.refetch).not.toHaveBeenCalled();
            expect(mockedPredictionsRoiQuery.refetch).not.toHaveBeenCalled();
        });
    });

    describe('task chain project', () => {
        const renderTaskChainApp = async (mode: ANNOTATOR_MODE, isTaskChainSecondTask: boolean) => {
            const mockedUseTask = mockedTaskContextProps({
                isTaskChainSecondTask,
            });
            jest.mocked(useProject).mockImplementation(() => mockedProjectContextProps({ isTaskChainProject: true }));
            const mockPredictionsQuery = { refetch: jest.fn() };
            const mockedPredictionsRoiQuery = { refetch: jest.fn() };
            const mockSelectedMediaItemQuery = { refetch: jest.fn() };

            const setSearchParamsSpy = await renderApp({
                mode,
                modelData: loadedModelData,
                mockPredictionsQuery,
                mockedPredictionsRoiQuery,
                mockSelectedMediaItemQuery,
                mockedUseTask,
            });

            return { mockPredictionsQuery, mockedPredictionsRoiQuery, mockSelectedMediaItemQuery, setSearchParamsSpy };
        };

        it('not segmentation task, selecting prediction mode refetch predictions', async () => {
            const { mockPredictionsQuery, mockedPredictionsRoiQuery, setSearchParamsSpy } = await renderTaskChainApp(
                ANNOTATOR_MODE.ACTIVE_LEARNING,
                false
            );

            expect(getPredictionButton()).toBeEnabled();
            expect(mockPredictionsQuery.refetch).not.toHaveBeenCalled();

            fireEvent.click(getPredictionButton());
            expect(setSearchParamsSpy).toHaveBeenCalledWith('mode', 'predictions');
            expect(mockedPredictionsRoiQuery.refetch).not.toHaveBeenCalled();
        });

        it('task-chain second task, selecting prediction mode refetch Roi predictions', async () => {
            const { mockPredictionsQuery, mockedPredictionsRoiQuery, mockSelectedMediaItemQuery } =
                await renderTaskChainApp(ANNOTATOR_MODE.ACTIVE_LEARNING, true);
            expect(getPredictionButton()).toBeEnabled();

            fireEvent.click(getPredictionButton());

            await waitFor(() => {
                expect(mockPredictionsQuery.refetch).not.toHaveBeenCalled();
                expect(mockedPredictionsRoiQuery.refetch).toHaveBeenCalledTimes(1);
                expect(mockSelectedMediaItemQuery.refetch).toHaveBeenCalled();
            });
        });

        it('selecting annotation mode not refetch predictions', async () => {
            const { mockPredictionsQuery, mockedPredictionsRoiQuery } = await renderTaskChainApp(
                ANNOTATOR_MODE.PREDICTION,
                false
            );

            fireEvent.click(getAnnotationButton());
            expect(mockPredictionsQuery.refetch).not.toHaveBeenCalled();
            expect(mockedPredictionsRoiQuery.refetch).not.toHaveBeenCalled();
        });
    });
});
