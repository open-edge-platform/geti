// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { renderHook } from '@testing-library/react';

import { Annotation, AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { Label } from '../../../../core/labels/label.interface';
import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { INITIAL_PROJECT_SETTINGS } from '../../../../core/user-settings/utils';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedImage } from '../../../../test-utils/utils';
import { SelectedMediaItem } from '../selected-media-item-provider/selected-media-item.interface';
import { useInitialAnnotation } from './use-initial-annotations.hook';

const useSettingsMock = getMockedUserProjectSettingsObject({
    saveConfig: jest.fn(),
    isSavingConfig: false,
    config: INITIAL_PROJECT_SETTINGS,
});

const mockLabel = (label: Partial<Label>, score = 1) =>
    ({
        ...getMockedLabel(label),
        score,
    }) as AnnotationLabel;

const mockAnnotation = getMockedAnnotation({ id: 'annotation-1', labels: [mockLabel({ id: '123' }, 0.01)] });
const mockPrediction = getMockedAnnotation({ id: 'prediction-1', labels: [mockLabel({ id: '123' }, 0.01)] });
const geSelectedMediaItem = (predictions: Annotation[] = [], annotations: Annotation[] = []): SelectedMediaItem => ({
    ...getMockedImageMediaItem({}),
    image: getMockedImage(),
    annotations,
    predictions: { annotations: predictions, maps: [] },
});
const getInitialPredictionConfig = (isEnabled = true) => ({
    [FEATURES_KEYS.INITIAL_PREDICTION]: {
        isEnabled,
        title: 'Initial Prediction',
        tooltipDescription: 'Turn off to skip loading predictions when opening an image.',
    },
});

describe('useInitialAnnotation', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('returns user annotations', async () => {
        const { result } = renderHook(() =>
            useInitialAnnotation(geSelectedMediaItem([], [mockAnnotation]), null, useSettingsMock, false)
        );

        expect(result.current).toEqual([mockAnnotation]);
    });

    it('use prediction as initial annotations', async () => {
        const { result } = renderHook(() =>
            useInitialAnnotation(geSelectedMediaItem([mockPrediction]), null, useSettingsMock, false)
        );

        expect(result.current).toEqual([mockPrediction]);
    });

    it('return empty if INITIAL_PREDICTION is disabled', async () => {
        const { result } = renderHook(() =>
            useInitialAnnotation(
                geSelectedMediaItem([mockPrediction]),
                null,
                {
                    ...useSettingsMock,
                    config: {
                        ...useSettingsMock.config,
                        ...getInitialPredictionConfig(false),
                    },
                },
                false
            )
        );

        expect(result.current).toEqual([]);
    });

    it('returns new annotations if number of predictions changes', async () => {
        const { result, rerender } = renderHook(
            ({ selectedMediaItem }) => useInitialAnnotation(selectedMediaItem, null, useSettingsMock, false),
            { initialProps: { selectedMediaItem: geSelectedMediaItem([]) } }
        );
        expect(result.current).toEqual([]);

        rerender({ selectedMediaItem: geSelectedMediaItem([mockPrediction]) });
        expect(result.current).toEqual([mockPrediction]);
    });
});
