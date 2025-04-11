// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
