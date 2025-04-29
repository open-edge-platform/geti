// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromModel, labelFromUser } from '../../../../core/annotations/utils';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { hasMediaPredictionChanges, shouldSaveAnnotations } from './utils';

const mockedLabel = labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' }));

const mockedAnnotation = getMockedAnnotation({ id: 'test-annotation' }, ShapeType.Rect);
const mockedPrediction = getMockedAnnotation(
    { id: 'test-annotation-prediction', labels: [mockedLabel] },
    ShapeType.Rect
);

describe('shouldSasubmit-annotations-provider utils', () => {
    it('shouldSaveAnnotations', () => {
        expect(shouldSaveAnnotations(undefined, [])).toBe(false);
        expect(shouldSaveAnnotations(undefined, [mockedAnnotation])).toBe(false);
        expect(shouldSaveAnnotations([mockedAnnotation], [mockedAnnotation])).toBe(false);
        expect(shouldSaveAnnotations([mockedAnnotation], [mockedPrediction])).toBe(true);

        // it does not ignore prediction labels
        const predictionLabels = [labelFromModel(getMockedLabel({}), 0.5, 'model-id', 'model-storage-id')];
        expect(shouldSaveAnnotations([mockedAnnotation], [{ ...mockedAnnotation, labels: predictionLabels }])).toBe(
            true
        );
    });

    describe('hasMediaPredictionChanges', () => {
        it('no media item', () => {
            expect(hasMediaPredictionChanges(undefined, undefined, [mockedAnnotation])).toBe(false);
        });

        it('annotations without changes', () => {
            expect(hasMediaPredictionChanges([mockedAnnotation], [], [mockedAnnotation])).toBe(false);
        });

        it('annotations with changes', () => {
            expect(hasMediaPredictionChanges([mockedAnnotation], [], [{ ...mockedAnnotation, id: 'new-id' }])).toBe(
                true
            );
        });

        it('suggestedAnnotations (prediction) without changes', () => {
            expect(hasMediaPredictionChanges([], [mockedPrediction], [mockedPrediction])).toBe(false);
        });

        it('suggestedAnnotations (prediction) with changes', () => {
            expect(
                hasMediaPredictionChanges(
                    [],
                    [mockedPrediction],
                    [{ ...mockedPrediction, zIndex: mockedPrediction.zIndex + 1 }]
                )
            ).toBe(true);
        });

        it('detection -> classification prediction', () => {
            const inputAnnotation = {
                ...mockedPrediction,
                labels: [labelFromUser(getMockedLabel({ id: 'card' }))],
            };
            const predictedAnnotation = {
                ...inputAnnotation,
                labels: [
                    ...inputAnnotation.labels,
                    labelFromModel(getMockedLabel({ id: 'spades' }), 0.33, 'model-id', 'storage-id'),
                ],
            };

            expect(hasMediaPredictionChanges([inputAnnotation], [predictedAnnotation], [predictedAnnotation])).toBe(
                false
            );
        });
    });
});
