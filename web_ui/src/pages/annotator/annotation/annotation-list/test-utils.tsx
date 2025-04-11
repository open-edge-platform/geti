// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactElement, ReactNode } from 'react';

import { RenderResult } from '@testing-library/react';
import { DragDropContext, Droppable, DroppableProvided } from 'react-beautiful-dnd';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender } from '../../../../test-utils/required-providers-render';

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

const RequiredAnnotationListItemProviders = ({ children }: { children?: ReactNode }) => {
    const handleDragEnd = jest.fn();

    return (
        <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId='annotation-droppable-id'>
                {(provided: DroppableProvided) => (
                    <div ref={provided.innerRef} {...provided.droppableProps}>
                        {children}
                    </div>
                )}
            </Droppable>
        </DragDropContext>
    );
};

const customRender = async (ui: ReactElement): Promise<RenderResult> =>
    providersRender(<RequiredAnnotationListItemProviders>{ui}</RequiredAnnotationListItemProviders>);

export { customRender as annotationItemRender };
