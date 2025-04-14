// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';
import { useControls } from 'react-zoom-pan-pinch';

import { FitImageToScreenButton } from './fit-image-to-screen-button.component';

jest.mock('react-zoom-pan-pinch', () => ({
    ...jest.requireActual('react-zoom-pan-pinch'),
    useControls: jest.fn(() => ({
        resetTransform: jest.fn(),
    })),
}));

describe('FitImageToScreen', () => {
    const resetTransformMock = jest.fn();

    it("Check if there is proper icon and if 'resetTransform' function is called after pressing", () => {
        // @ts-expect-error we mock only resetTransform function
        jest.mocked(useControls).mockImplementation(() => ({
            resetTransform: resetTransformMock,
        }));

        render(<FitImageToScreenButton />);

        expect(screen.getByText('fit-screen.svg')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Fit image to screen' }));

        expect(resetTransformMock).toHaveBeenCalled();
    });
});
