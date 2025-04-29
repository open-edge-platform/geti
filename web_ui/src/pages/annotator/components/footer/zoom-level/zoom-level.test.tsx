// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';
import { TransformComponent, useControls } from 'react-zoom-pan-pinch';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ZoomProvider } from '../../../zoom/zoom-provider.component';
import { ZoomLevel } from './zoom-level.component';

jest.mock('react-zoom-pan-pinch', () => ({
    ...jest.requireActual('react-zoom-pan-pinch'),
    useControls: jest.fn(() => ({
        resetTransform: jest.fn(),
        zoomIn: jest.fn(),
        zoomOut: jest.fn(),
    })),
}));

describe('zoom level', () => {
    it('displays the zoom level used to display the media item', () => {
        render(
            <ZoomProvider>
                <ZoomLevel zoom={0.33812} />
                <TransformComponent>{''}</TransformComponent>
            </ZoomProvider>
        );

        const zoomLevel = screen.getByTestId('zoom-level');

        expect(zoomLevel).toHaveAttribute('data-value', '0.33812');
        expect(zoomLevel).toHaveTextContent('34%');
        expect(zoomLevel).toHaveAttribute('id', 'footer-zoom-display');
    });

    it('zooms in/out correctly when using the buttons', () => {
        const mockResetTransform = jest.fn();
        const mockZoomIn = jest.fn();
        const mockZoomOut = jest.fn();

        // @ts-expect-error we mock only resetTransform, zoomIn and zoomOut functions
        jest.mocked(useControls).mockImplementation(() => ({
            resetTransform: mockResetTransform,
            zoomIn: mockZoomIn,
            zoomOut: mockZoomOut,
        }));

        render(
            <ZoomProvider>
                <TransformComponent>
                    <ZoomLevel zoom={1} />
                </TransformComponent>
            </ZoomProvider>
        );

        const zoomLevel = screen.getByTestId('zoom-level');

        expect(zoomLevel).toHaveAttribute('data-value', '1');
        expect(zoomLevel).toHaveTextContent('100%');
        expect(zoomLevel).toHaveAttribute('id', 'footer-zoom-display');

        fireEvent.click(screen.getByLabelText('Zoom in'));
        fireEvent.click(screen.getByLabelText('Zoom in'));

        expect(mockZoomIn).toHaveBeenCalledTimes(2);

        fireEvent.click(screen.getByLabelText('Zoom out'));
        expect(mockZoomOut).toHaveBeenCalledTimes(1);
    });
});
