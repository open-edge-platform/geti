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

import { renderHook } from '@testing-library/react';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { Shape } from '../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { getLabeledShape } from '../utils';
import { useAddUnfinishedShape } from './use-add-unfinished-shape.hook';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useLocation: jest.fn(),
}));

const annotations: Annotation[] = [];
let unfinishedShapeCallback: (() => void) | null = null;
const mockSetUnfinishedShapeCallback = jest.fn((callback) => (unfinishedShapeCallback = callback));
jest.mock('../providers/submit-annotations-provider/submit-annotations-provider.component', () => ({
    ...jest.requireActual('../providers/submit-annotations-provider/submit-annotations-provider.component'),
    useSubmitAnnotations: () => ({ setUnfinishedShapeCallback: mockSetUnfinishedShapeCallback }),
}));

jest.mock('../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    ...jest.requireActual('../providers/annotation-scene-provider/annotation-scene-provider.component'),
    useAnnotationScene: () => ({ annotations }),
}));

const newShape: Shape = {
    shapeType: ShapeType.Polygon,
    points: [],
};
const addShapes = jest.fn();

describe('useAddUnfinishedShape', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        unfinishedShapeCallback = null;
    });

    it('setUnfinishedShapeCallback is called with null', () => {
        const shapes: Shape[] = [];
        renderHook(() => useAddUnfinishedShape({ addShapes, shapes, reset: jest.fn() }));

        expect(unfinishedShapeCallback).toBeNull();
        expect(mockSetUnfinishedShapeCallback).toHaveBeenCalledWith(null);
    });

    it('setUnfinishedShapeCallback is set with valid callback', () => {
        const reset = jest.fn();
        const shapes: Shape[] = [newShape, newShape];
        const newAnnotationMock = shapes.map((shape, idx) => getLabeledShape('', shape, [], true, shapes.length + idx));
        addShapes.mockReturnValueOnce(newAnnotationMock);

        renderHook(() => useAddUnfinishedShape({ addShapes, shapes, reset }));

        const newAnnotation = unfinishedShapeCallback && unfinishedShapeCallback();

        expect(reset).toHaveBeenCalled();
        expect(newAnnotation).toEqual(newAnnotationMock);
        expect(addShapes).toHaveBeenCalledWith(shapes);
        expect(mockSetUnfinishedShapeCallback).toHaveBeenCalledWith(expect.any(Function));
    });

    it('component unmounted, save the current shape', async () => {
        const shapes: Shape[] = [newShape, newShape];
        const { unmount } = renderHook(() => useAddUnfinishedShape({ addShapes, shapes, reset: jest.fn() }));
        unmount();

        expect(unfinishedShapeCallback).toBeNull();
        expect(addShapes).toHaveBeenCalledWith(shapes);
    });

    it('component unmounted with empty shape', async () => {
        const { unmount } = renderHook(() => useAddUnfinishedShape({ addShapes, shapes: [], reset: jest.fn() }));
        unmount();

        expect(unfinishedShapeCallback).toBeNull();
        expect(addShapes).not.toHaveBeenCalled();
    });
});
