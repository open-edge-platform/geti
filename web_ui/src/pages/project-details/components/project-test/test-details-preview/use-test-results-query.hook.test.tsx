// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';

import { Explanation } from '../../../../../core/annotations/prediction.interface';
import { createInMemoryInferenceService } from '../../../../../core/annotations/services/in-memory-inference-service';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { TestMediaItem } from '../../../../../core/tests/test-media.interface';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import {
    getMockedDatasetIdentifier,
    getMockedProjectIdentifier,
} from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImageMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { RequiredProviders } from '../../../../../test-utils/required-providers-render';
import { TaskProvider } from '../../../../annotator/providers/task-provider/task-provider.component';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { useTestResultsQuery } from './use-test-results-query.hook';

const mockedInferenceService = createInMemoryInferenceService();
const mockAnnotation = getMockedAnnotation({
    id: 'test-annotation-2',
    isSelected: true,
    shape: { shapeType: ShapeType.Rect, height: 50, width: 50, x: 0, y: 0 },
    labels: [],
});
mockedInferenceService.getTestPredictions = jest.fn();
mockedInferenceService.getExplanations = jest.fn();
mockedInferenceService.getInferenceServerStatus = async () => ({ isInferenceServerReady: true });

const wrapper = ({ children }: { children?: ReactNode }) => (
    <RequiredProviders inferenceService={mockedInferenceService}>
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>{children}</TaskProvider>
        </ProjectProvider>
    </RequiredProviders>
);

describe('useTestResultsQuery', () => {
    const datasetIdentifier = getMockedDatasetIdentifier();
    const media = getMockedImageMediaItem({
        identifier: {
            imageId: '60b609fbd036ba4566726c96',
            type: MEDIA_TYPE.IMAGE,
        },
    });
    const mockedTestMediaItem = {
        type: MEDIA_TYPE.IMAGE,
        media,
        testResult: { predictionId: '123', annotationId: '321', scores: [] },
    } as TestMediaItem;

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('calls inference service "getTestPredictions"', async () => {
        renderHook(() => useTestResultsQuery(datasetIdentifier, media, mockedTestMediaItem, '123'), {
            wrapper,
        });

        await waitFor(() => {
            expect(mockedInferenceService.getExplanations).toHaveBeenCalled();
            expect(mockedInferenceService.getTestPredictions).toHaveBeenCalled();
        });
    });

    it('still returns valid data if the explanation call fails', async () => {
        mockedInferenceService.getTestPredictions = jest.fn(() => Promise.resolve([mockAnnotation]));
        mockedInferenceService.getExplanations = jest.fn(() => Promise.reject(new Error()));

        const { result } = renderHook(() => useTestResultsQuery(datasetIdentifier, media, mockedTestMediaItem, '123'), {
            wrapper,
        });

        await waitFor(() => {
            expect(mockedInferenceService.getExplanations).toHaveBeenCalled();
            expect(mockedInferenceService.getTestPredictions).toHaveBeenCalled();
            expect(result.current.predictionsQuery.data).toEqual({ annotations: [mockAnnotation], maps: [] });
        });
    });

    it('still returns valid data if the prediction call fails', async () => {
        const mockedExplanation: Explanation = {
            id: 'mocked-explanation',
            labelsId: 'mocked-label-id',
            name: 'mocked-explanation',
            roi: { id: 'roi-id-1', shape: { type: 'RECTANGLE', x: 0, y: 0, width: 100, height: 100 } },
            url: 'https://example.com',
        };

        mockedInferenceService.getTestPredictions = jest.fn(() => Promise.reject(new Error()));
        mockedInferenceService.getExplanations = jest.fn(() => Promise.resolve([mockedExplanation]));

        const { result } = renderHook(() => useTestResultsQuery(datasetIdentifier, media, mockedTestMediaItem, '123'), {
            wrapper,
        });

        await waitFor(() => {
            expect(mockedInferenceService.getExplanations).toHaveBeenCalled();
            expect(mockedInferenceService.getTestPredictions).toHaveBeenCalled();
            expect(result.current.predictionsQuery.data).toEqual({ annotations: [], maps: [mockedExplanation] });
        });
    });
});
