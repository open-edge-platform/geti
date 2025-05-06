// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';

export const defaultAnnotationState: Annotation[] = [
    getMockedAnnotation(
        {
            id: '1',
            zIndex: 0,
            labels: [
                labelFromUser(getMockedLabel({ id: '1', name: 'dog', color: 'red' })),
                labelFromUser(getMockedLabel({ id: '2', name: 'cat', color: 'red' })),
            ],
        },
        ShapeType.Circle
    ),
    getMockedAnnotation(
        {
            id: '2',
            zIndex: 1,
            labels: [
                labelFromUser(getMockedLabel({ id: '1', name: 'parrot', color: 'red' })),
                labelFromUser(getMockedLabel({ id: '2', name: 'pig', color: 'red' })),
            ],
        },
        ShapeType.Rect
    ),
];

export const selectedLockedAnnotation = getMockedAnnotation({
    id: 'selected-locked-annotation',
    isSelected: true,
    isLocked: true,
});

export const selectedAnnotation = getMockedAnnotation({
    id: 'selected-unlocked-annotation',
    isSelected: true,
});

export const selectedHiddenAnnotation = getMockedAnnotation({
    id: 'selected-hidden-annotation',
    isSelected: true,
    isHidden: true,
});

export const notSelectedAnnotation = getMockedAnnotation({
    id: 'not-selected-annotation',
});
