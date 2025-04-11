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

import '@wessberg/pointer-events';

import { fireEvent, screen } from '@testing-library/react';

import { getBoundingBox } from '../../../../core/annotations/math';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../providers/task-chain-provider/task-chain-provider.component';
import { DrawingBox } from './drawing-box.component';

const mockROI = { x: 0, y: 0, width: 200, height: 200 };
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../providers/task-chain-provider/task-chain-provider.component', () => ({
    ...jest.requireActual('../../providers/task-chain-provider/task-chain-provider.component'),
    useTaskChain: jest.fn(() => ({ inputs: [], outputs: [] })),
}));

describe('SelectingTool', () => {
    const drawRect = (x: number, y: number, width: number, height: number) => {
        const svg = screen.getByRole('editor');

        fireEvent.pointerMove(svg, { clientX: x, clientY: y });
        fireEvent.pointerDown(svg, { buttons: 1, clientX: x, clientY: y });

        const rect = screen.getByRole('application');
        expect(rect).toHaveAttribute('x', `${x}`);
        expect(rect).toHaveAttribute('y', `${y}`);
        expect(rect).toHaveAttribute('width', '0');
        expect(rect).toHaveAttribute('height', '0');

        fireEvent.pointerMove(svg, { clientX: x + width, clientY: y + height });
        fireEvent.pointerUp(svg);
    };

    it('draws a bounding box', () => {
        const onStart = jest.fn();
        const onComplete = jest.fn();
        render(
            <DrawingBox image={mockImage} zoom={1} onStart={onStart} onComplete={onComplete} withCrosshair={false} />
        );

        drawRect(50, 50, 100, 100);

        expect(onComplete).toHaveBeenCalledWith({
            shapeType: ShapeType.Rect,
            x: 50,
            y: 50,
            width: 100,
            height: 100,
        });
    });

    it('limits the bounding box based on the image size', () => {
        const onStart = jest.fn();
        const onComplete = jest.fn();
        render(
            <DrawingBox image={mockImage} zoom={1} onStart={onStart} onComplete={onComplete} withCrosshair={false} />
        );

        drawRect(50, 50, 400, 400);
        expect(onComplete).toHaveBeenCalledWith({
            shapeType: ShapeType.Rect,
            x: 50,
            y: 50,
            width: 150,
            height: 150,
        });
    });

    it('limits the bounding box based on the selected input annotation', () => {
        const onStart = jest.fn();
        const onComplete = jest.fn();

        const inputShape = {
            shapeType: ShapeType.Rect as const,
            x: 50,
            y: 50,
            width: 150,
            height: 150,
        };

        const inputs = [{ ...getMockedAnnotation({ isSelected: true, shape: inputShape }), outputs: [] }];

        jest.mocked(useTaskChain).mockImplementation(() => ({
            inputs,
            outputs: [],
        }));

        jest.mocked(useROI).mockReturnValue({ image: mockImage, roi: getBoundingBox(inputs[0].shape) });

        render(
            <DrawingBox image={mockImage} zoom={1} onStart={onStart} onComplete={onComplete} withCrosshair={false} />
        );

        // The output should be constrained with respect to the input shape
        drawRect(0, 0, 400, 400);
        expect(onComplete).toHaveBeenCalledWith({
            shapeType: ShapeType.Rect,
            x: 50,
            y: 50,
            width: 150,
            height: 150,
        });
    });
});
