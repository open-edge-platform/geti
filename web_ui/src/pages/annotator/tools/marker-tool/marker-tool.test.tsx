// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
