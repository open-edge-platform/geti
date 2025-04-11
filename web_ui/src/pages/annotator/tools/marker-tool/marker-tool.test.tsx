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

import '@wessberg/pointer-events';

import { fireEvent, render, screen } from '@testing-library/react';

import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedImage } from '../../../../test-utils/utils';
import { MarkerTool } from './marker-tool.component';

describe('MarkerTool', () => {
    const image = getMockedImage();
    const zoom = 1;

    it('renders a polyline correctly', () => {
        const mockOnComplete = jest.fn();
        const mockLabel = getMockedLabel({ name: 'label 1', color: 'red' });

        const { container } = render(
            <MarkerTool
                markerId={1}
                zoom={zoom}
                image={image}
                brushSize={4}
                label={mockLabel}
                onComplete={mockOnComplete}
            />
        );

        const svg = screen.getByRole('editor');

        fireEvent.pointerDown(svg, { clientX: 4, clientY: 42, button: 0, buttons: 1 });
        fireEvent.pointerMove(svg, { clientX: 5, clientY: 43, button: 0, buttons: 1 });

        const polyline = container.querySelector('polyline');

        expect(polyline).toHaveAttribute('points', '4,42 5,43');
    });

    it('calls onComplete with the correct marker', () => {
        const mockOnComplete = jest.fn();
        const mockLabel = getMockedLabel({ name: 'label 1', color: 'green' });

        render(
            <MarkerTool
                markerId={2}
                zoom={zoom}
                image={image}
                brushSize={4}
                label={mockLabel}
                onComplete={mockOnComplete}
            />
        );

        const svg = screen.getByRole('editor');

        fireEvent.pointerDown(svg, { clientX: 4, clientY: 42, button: 0, buttons: 1 });
        fireEvent.pointerMove(svg, { clientX: 5, clientY: 43, button: 0, buttons: 1 });
        fireEvent.pointerUp(svg);

        expect(mockOnComplete).toHaveBeenCalledWith({
            brushSize: 4,
            id: 2,
            label: mockLabel,
            points: [
                { x: 4, y: 42 },
                { x: 5, y: 43 },
            ],
        });
    });
});
