// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { MEDIA_TYPE } from '../../../media/base-media.interface';
import { TaskChainInput } from '../../annotation.interface';
import { ShapeType } from '../../shapetype.enum';
import { getBatchPredictionsResponse, mockedBatchPredictionShape } from '../mockResponses';
import { convertPredictionLabelDTO } from '../utils';
import { BatchPredictionDTO, convertBatchToRecord, getExplanationRoi, getInputShapeRect, hasEmptyLabel } from './utils';

const roiShape = { x: 10, y: 10, width: 50, height: 50 };
const labelOne = getMockedLabel({ id: '123', name: 'card' });
const emptyLabel = getMockedLabel({ id: '321', name: 'Empty', isEmpty: true });
const PROJECT_LABELS = [labelOne, emptyLabel];
const predictionLabelOne = convertPredictionLabelDTO({ ...labelOne, probability: 1 });
const predictionLabelEmpty = convertPredictionLabelDTO({ ...emptyLabel, probability: 1 });
const mockedImageMedia = getMockedImageMediaItem({
    identifier: { imageId: '60b609fbd036ba4566726c96', type: MEDIA_TYPE.IMAGE },
});

const taskChainInput = getMockedAnnotation({
    id: 'taskChainInput-id',
    shape: { shapeType: ShapeType.Rect, ...roiShape },
}) as TaskChainInput;

const mockedBatchPredictionsLabelOne = getBatchPredictionsResponse(labelOne).batch_predictions as BatchPredictionDTO[];

describe('api-inference-service-utils', () => {
    it('getInputShapeRect', () => {
        expect(getInputShapeRect(taskChainInput)).toEqual(roiShape);
    });

    it('hasEmptyLabel', () => {
        expect(hasEmptyLabel(PROJECT_LABELS)(predictionLabelOne)).toBe(false);
        expect(hasEmptyLabel(PROJECT_LABELS)(predictionLabelEmpty)).toBe(true);
    });

    it('getExplanationRoi', () => {
        expect(getExplanationRoi(mockedImageMedia)).toEqual({
            y: 0,
            x: 0,
            id: expect.any(String),
            height: mockedImageMedia.metadata.height,
            width: mockedImageMedia.metadata.width,
        });

        expect(getExplanationRoi(mockedImageMedia, taskChainInput)).toEqual({
            id: taskChainInput.id,
            ...roiShape,
        });
    });

    it('convertBatchToRecord', () => {
        const { type, ...expectedShape } = mockedBatchPredictionShape;
        const label = {
            ...labelOne,
            score: 0.1,
            source: { modelId: 'latest', modelStorageId: 'storage_id', userId: undefined },
        };

        const batchRecord = {
            id: expect.any(String),
            isHidden: false,
            isLocked: false,
            isSelected: false,
            labels: [label],
            shape: { ...expectedShape, shapeType: 1 },
            zIndex: 0,
        };

        expect(convertBatchToRecord([null, ...mockedBatchPredictionsLabelOne, null], PROJECT_LABELS)).toEqual({
            '0': [batchRecord],
            '10': [{ ...batchRecord, labels: [{ ...label, score: 0.2 }] }],
        });
    });
});
