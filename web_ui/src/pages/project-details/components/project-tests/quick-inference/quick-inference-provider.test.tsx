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

import { ReactNode } from 'react';

import { act, waitFor } from '@testing-library/react';
import isFunction from 'lodash/isFunction';

import { Explanation } from '../../../../../core/annotations/prediction.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import * as MediaValidators from '../../../../../providers/media-upload-provider/media-upload.validator';
import { validateMedia } from '../../../../../providers/media-upload-provider/media-upload.validator';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { renderHookWithProviders } from '../../../../../test-utils/render-hook-with-providers';
import { QuickInferenceProvider, useQuickInference } from './quick-inference-provider.component';
import { useQuickInferenceMutation } from './use-quick-inference-mutation.hook';

jest.mock('./use-quick-inference-mutation.hook', () => ({ useQuickInferenceMutation: jest.fn() }));

jest.mock('../../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../../notification/notification.component'),
    useNotification: jest.fn().mockImplementation(() => ({ addNotification: jest.fn() })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
        projectId: 'project-id',
    }),
}));

const wrapper = ({ children }: { children?: ReactNode }) => {
    return <QuickInferenceProvider isDisabled={false}>{children}</QuickInferenceProvider>;
};

const mockQuickInferenceMutation = (properties: Record<string, unknown> = {}) => {
    const mock = {
        predictionMutation: {
            isPending: false,
            mutate: jest.fn(),
            ...properties,
        },
        explainMutation: {
            isPending: false,
            isSuccess: true,
            mutate: jest.fn((...[_variables, options]) => {
                isFunction(options.onSuccess) && options.onSuccess(properties.data ?? { maps: [] });
            }),
            ...properties,
        },
        quickInferenceMutation: {
            isPending: false,
            mutate: jest.fn((...[_variables, options]) => {
                isFunction(options.onSuccess) && options.onSuccess(properties.data ?? { maps: [] });
            }),
            ...properties,
        },
    };

    (useQuickInferenceMutation as jest.Mock).mockImplementation(() => mock);

    return mock;
};

const fakeFile = (extension = 'jpg') => {
    const file = new File([new ArrayBuffer(1)], `file.${extension}`);

    Object.defineProperty(file, 'type', { value: `image/${extension}` });

    return file;
};

const projectIdentifier = { organizationId: 'organization-id', projectId: 'project-id', workspaceId: 'workspace_1' };
const mockedExplanation: Explanation = {
    id: 'mocked-explanation',
    labelsId: 'mocked-label-id',
    name: 'mocked-explanation',
    roi: { id: 'roi-id-1', shape: { type: 'RECTANGLE', x: 0, y: 0, width: 100, height: 100 } },
    url: 'https://example.com',
};

describe('Quick Inference Provider', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    beforeAll(() => {
        jest.spyOn(MediaValidators, 'validateMedia').mockImplementation((file) => Promise.resolve(file));
    });

    describe('setShowExplanation', () => {
        it('executes with explain when toggling on the explanation', () => {
            const file = fakeFile();
            const variables = { file, explain: false };
            const { explainMutation, predictionMutation } = mockQuickInferenceMutation({
                variables,
            });
            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            act(() => {
                result.current.setShowExplanation(true);
            });

            expect(explainMutation.mutate).toHaveBeenCalledWith(
                expect.objectContaining({ file, projectIdentifier }),
                expect.anything()
            );
            expect(predictionMutation.mutate).not.toHaveBeenCalled();
        });

        it('does not execute when toggling on when previous execution already had explain', () => {
            const file = fakeFile();
            const variables = { file, explain: true };
            const { explainMutation, predictionMutation } = mockQuickInferenceMutation({ variables });
            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            act(() => {
                result.current.setExplanation(mockedExplanation);
            });

            act(() => {
                result.current.setShowExplanation(true);
            });

            expect(explainMutation.mutate).not.toHaveBeenCalled();
            expect(predictionMutation.mutate).not.toHaveBeenCalled();
        });

        it('does not execute when no file is uploaded', () => {
            const { explainMutation, predictionMutation } = mockQuickInferenceMutation();
            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            act(() => {
                result.current.setShowExplanation(true);
            });

            expect(explainMutation.mutate).not.toHaveBeenCalled();
            expect(predictionMutation.mutate).not.toHaveBeenCalled();
        });
    });

    describe('handleUploadImage', () => {
        const file = new File(['hello'], 'hello.png', { type: 'image/png' });

        it('takes file and runs quick inference', async () => {
            const { predictionMutation, explainMutation } = mockQuickInferenceMutation({});
            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            result.current.handleUploadImage([file]);

            await waitFor(() => {
                expect(result.current.showExplanation).toBeFalsy();
                expect(predictionMutation.mutate).toHaveBeenCalledWith(
                    expect.objectContaining({ file, projectIdentifier })
                );
                expect(explainMutation.mutate).not.toHaveBeenCalled();
            });
        });

        it('sets image with uploaded image', async () => {
            mockQuickInferenceMutation();

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            result.current.handleUploadImage([file]);

            await waitFor(() => {
                expect(result.current.image).toBeDefined();
            });
        });

        it('sets show prediction on if predictions are hidden', async () => {
            mockQuickInferenceMutation();

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            result.current.handleUploadImage([file]);

            await waitFor(() => {
                expect(result.current.showPredictions).toBeTruthy();
            });
        });

        it('uploaded media is validated', async () => {
            (validateMedia as jest.Mock).mockReset();

            mockQuickInferenceMutation();

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            result.current.handleUploadImage([file]);

            await waitFor(() => {
                expect(validateMedia).toBeCalledWith(file);
            });
        });
    });

    describe('annotations', () => {
        it('returns list of annotations from quickInferenceMutation', () => {
            const mockedAnnotation = getMockedAnnotation({}, ShapeType.Rect);
            mockQuickInferenceMutation({
                isSuccess: true,
                data: [mockedAnnotation],
            });

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            act(() => {
                result.current.toggleShowPredictions();
            });

            expect(result.current.annotations).toEqual([mockedAnnotation]);
        });

        it('returns list empty list of annotations when showPredictions is off', () => {
            const mockedAnnotation = getMockedAnnotation({}, ShapeType.Rect);
            mockQuickInferenceMutation({
                isSuccess: true,
                data: [mockedAnnotation],
            });

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            expect(result.current.showPredictions).toBeFalsy();
            expect(result.current.annotations).toEqual([]);
        });

        it('returns list empty list of annotations if quickInference was unsuccessful', () => {
            const mockedAnnotation = getMockedAnnotation({}, ShapeType.Rect);
            mockQuickInferenceMutation({
                isSuccess: false,
                data: [mockedAnnotation],
            });

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            act(() => {
                result.current.toggleShowPredictions();
            });

            expect(result.current.annotations).toEqual([]);
        });
    });

    describe('showWarningCard', () => {
        beforeEach(() => {
            mockQuickInferenceMutation({
                isSuccess: false,
                isError: false,
                failureCount: 1,
            });
        });

        it('is false when card is dismissed', () => {
            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            act(() => {
                result.current.dismissWarningCard();
            });

            expect(result.current.showWarningCard).toBeFalsy();
        });

        it('is true when quickInference was neither successful nor an error occurred', () => {
            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            expect(result.current.showWarningCard).toBeTruthy();
        });
    });

    describe('isLoading', () => {
        it('is true when quickInferenceMutation is loading', () => {
            mockQuickInferenceMutation({
                isPending: true,
            });

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            expect(result.current.isLoading).toBeTruthy();
        });
    });

    describe('explanations', () => {
        it('returns the list of explanations from quickInferenceMutation', () => {
            mockQuickInferenceMutation({
                data: [mockedExplanation],
            });

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            expect(result.current.explanations).toEqual([mockedExplanation]);
        });

        it('returns empty list when no mutation', () => {
            mockQuickInferenceMutation({
                data: undefined,
            });

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            expect(result.current.explanations).toEqual([]);
        });

        it('returns sorted list of maps based on map name', () => {
            const mapA = { ...mockedExplanation, name: 'a-map' };
            const mapB = { ...mockedExplanation, name: 'z-map' };

            mockQuickInferenceMutation({ data: [mapB, mapA] });

            const { result } = renderHookWithProviders(() => useQuickInference(), { wrapper });

            expect(result.current.explanations).toEqual([mapA, mapB]);
        });
    });
});
