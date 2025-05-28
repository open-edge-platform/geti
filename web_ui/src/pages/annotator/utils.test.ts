// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Explanation } from '../../core/annotations/prediction.interface';
import { Rect } from '../../core/annotations/shapes.interface';
import { ShapeType } from '../../core/annotations/shapetype.enum';
import { Label } from '../../core/labels/label.interface';
import { DOMAIN } from '../../core/projects/core.interface';
import { getMockedAnnotation } from '../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../test-utils/mocked-items-factory/mocked-labels';
import {
    areAnnotationsIdentical,
    areLabelsIdentical,
    createAnnotation,
    filterForExplanation,
    filterForSelectedTask,
    filterHidden,
    filterIfInEditMode,
    getLabeledShape,
    getPercentage,
    getPredictionAnnotations,
} from './utils';

describe('Annotator utils', () => {
    describe('filterHidden', () => {
        it('removes hidden annotations from list', () => {
            const shownAnnotations = [getMockedAnnotation({ id: 'test-prediction-annotation' })];
            const hiddenAnnotations = [getMockedAnnotation({ id: 'hidden-prediction-annotation', isHidden: true })];
            expect([...shownAnnotations, ...hiddenAnnotations].filter(filterHidden)).toEqual(shownAnnotations);
        });
    });

    describe('filterForSelectedTask', () => {
        it('returns only selected for classification', () => {
            const selectedAnnotations = [getMockedAnnotation({ id: 'selected', isSelected: true })];
            const annotations = [...selectedAnnotations, getMockedAnnotation({ id: 'not-selected' })];
            expect(annotations.filter(filterForSelectedTask(DOMAIN.CLASSIFICATION))).toEqual(selectedAnnotations);
        });

        const allDomainsExceptForClassification = Object.keys(DOMAIN).filter((m) => m !== DOMAIN.CLASSIFICATION);
        const selectedAnnotations = [getMockedAnnotation({ id: 'selected', isSelected: true })];
        const annotations = [...selectedAnnotations, getMockedAnnotation({ id: 'not-selected' })];

        test.each(allDomainsExceptForClassification)('returns all for domain %s', (domain) => {
            expect(annotations.filter(filterForSelectedTask(domain as DOMAIN))).toEqual(annotations);
        });
    });

    describe('filterForExplanation', () => {
        const mockRoi = { id: 'roi-1', shape: { x: 0, y: 0, width: 100, height: 100, type: 'RECTANGLE' } };
        const label1 = { ...getMockedLabel(), source: {} };

        const label1Annotations = [getMockedAnnotation({ id: 'label1-annotation', labels: [label1] })];
        const annotations = [...label1Annotations, getMockedAnnotation({ id: 'without label' })];

        describe('explanation With Label Id', () => {
            const explanation: Explanation = {
                id: '6138bca43b7b11505c43f2c1',
                labelsId: label1.id,
                name: 'Lorem',
                roi: mockRoi,
                url: 'https://placekitten.com/g/600/400',
            };
            it('shows only annotations with that label', () => {
                expect(annotations.filter(filterForExplanation(explanation, true))).toEqual(label1Annotations);
            });
            it('shows all annotations if filter is not on', () => {
                expect(annotations.filter(filterForExplanation(explanation, false))).toEqual(annotations);
            });
        });

        describe('explanation without Label Id', () => {
            const explanation: Explanation = {
                id: '6138bca43b7b11505c43f2c1',
                labelsId: '',
                name: 'Lorem',
                roi: mockRoi,
                url: 'https://placekitten.com/g/600/400',
            };
            it('shows all annotations', () => {
                expect(annotations.filter(filterForExplanation(explanation, true))).toEqual(annotations);
            });
        });

        describe('undefined explanation', () => {
            const explanation = undefined;
            it('shows all annotations', () => {
                expect(annotations.filter(filterForExplanation(explanation, true))).toEqual(annotations);
            });
        });
    });

    describe('filterIfInEditMode', () => {
        const selectedAnnotations = [getMockedAnnotation({ id: 'selected', isSelected: true })];

        const selectedAndLockedAnnotations = [
            getMockedAnnotation({ id: 'selected-and-locked', isSelected: true, isLocked: true }),
        ];
        const notSelected = [getMockedAnnotation({ id: 'not-selected' })];
        describe('is in edit mode', () => {
            test('returns only not selected', () => {
                const ann = [...selectedAnnotations, ...notSelected];

                expect(ann.filter(filterIfInEditMode(true))).toEqual(notSelected);
            });
            test('returns selected and locked', () => {
                expect(selectedAndLockedAnnotations.filter(filterIfInEditMode(true))).toEqual(
                    selectedAndLockedAnnotations
                );
            });
        });

        describe('not in edit mode', () => {
            const annotations = [...selectedAnnotations, ...selectedAndLockedAnnotations, ...notSelected];
            it('returns all annotations', () => {
                expect(annotations.filter(filterIfInEditMode(false))).toEqual(annotations);
            });
        });
    });

    it('createAnnotation', () => {
        const shape = { shapeType: ShapeType.Rect, x: 0, y: 10, width: 100, height: 110 } as Rect;

        expect(createAnnotation(shape, [])).toEqual({
            id: expect.any(String),
            shape,
            zIndex: 0,
            labels: [],
            isHidden: false,
            isLocked: false,
            isSelected: false,
        });
    });

    it('getLabeledShape', () => {
        const id = '123';
        const shape = { shapeType: ShapeType.Rect, x: 0, y: 10, width: 100, height: 110 } as Rect;

        expect(getLabeledShape(id, shape, [], true, 1)).toEqual({
            id,
            shape,
            zIndex: 1,
            labels: [],
            isHidden: false,
            isLocked: false,
            isSelected: true,
        });
    });

    it('areAnnotationsIdentical', () => {
        expect(
            areAnnotationsIdentical([getMockedAnnotation({ id: '123' })], [getMockedAnnotation({ id: '321' })])
        ).toBe(false);

        expect(
            areAnnotationsIdentical(
                [getMockedAnnotation({ id: '123', isSelected: true, isLocked: true, isHidden: false })],
                [getMockedAnnotation({ id: '123', isSelected: false, isLocked: false, isHidden: true })]
            )
        ).toBe(true);

        // When adding a label it may happen that the UI adds additional propertires to an annotation's
        // label information, we want to make sure this gets ignored.
        const label = {
            id: '65a6ba799fac25e28e263cce',
            name: 'Object',
            color: '#708541ff',
            group: 'Detection labels',
            parentLabelId: null,
            source: {
                userId: '39dfb913-76a2-4cbc-abf9-d1ce5ba1938a',
            },
            hotkey: '',
            behaviour: 2,
            isEmpty: false,
            isBackground: false,
        };
        const labelWithExtras = {
            ...label,
            open: false,
            children: [],
            inEditMode: false,
            type: 'LABEL',
            state: 'Idle',
            relation: 'Single selection',
        };

        const annotation = getMockedAnnotation({ id: '123', labels: [] });
        expect(
            areAnnotationsIdentical(
                [{ ...annotation, labels: [label] }],
                [{ ...annotation, labels: [labelWithExtras] }]
            )
        ).toBe(true);

        expect(
            areAnnotationsIdentical(
                [{ ...annotation, labels: [label] }],
                [{ ...annotation, labels: [{ ...label, score: 0.33 }] }]
            )
        ).toBe(false);
    });

    it('areLabelsIdentical', () => {
        const annotationLabel = (label?: Partial<Label>) => ({
            ...getMockedLabel(label),
            source: { userId: 'user-email@test.com', modelId: undefined, modelStorageId: undefined },
        });

        expect(areLabelsIdentical([annotationLabel({ color: 'red' })], [annotationLabel({ color: 'blue' })])).toBe(
            true
        );

        expect(areLabelsIdentical([annotationLabel({ id: '123' })], [annotationLabel({ id: '321' })])).toBe(false);
    });

    it('getPercentage', () => {
        expect(getPercentage(0)).toEqual('100%');
    });

    it('getPredictionAnnotations', () => {
        const userAnnotation = getMockedAnnotation(
            {
                labels: [{ ...getMockedLabel({}), source: { userId: '123321' } }],
            },
            ShapeType.Rect
        );

        const predictionAnnotation = getMockedAnnotation(
            {
                labels: [{ ...getMockedLabel({}), source: { modelId: '123' }, score: 0.9 }],
            },
            ShapeType.Rect
        );

        expect(getPredictionAnnotations([userAnnotation, predictionAnnotation])).toEqual([predictionAnnotation]);
    });
});
