// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
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

import { RotationAnchor, RotationAnchorProps } from './rotation-anchor.component';

describe('RotationAnchor Component', () => {
    const renderApp = ({
        zoom = 1,
        size = 5,
        pivot = { x: 50, y: 50 },
        position = { x: 70, y: 70 },
        basePosition = { x: 70, y: 70 },
        onComplete = jest.fn(),
        onMoveAnchorTo = jest.fn(),
    }: Partial<RotationAnchorProps>) => {
        render(
            <svg>
                <RotationAnchor
                    size={size}
                    zoom={zoom}
                    position={position}
                    basePosition={basePosition}
                    pivot={pivot}
                    onComplete={onComplete}
                    onMoveAnchorTo={onMoveAnchorTo}
                />
            </svg>
        );
    };

    it('invokes onMoveAnchorTo with the updated angle', () => {
        const pivot = { x: 15, y: 15 };
        const position = { x: 10, y: 10 };
        const mockedOnComplete = jest.fn();
        const mockedOnMoveAnchorTo = jest.fn();
        renderApp({ onMoveAnchorTo: mockedOnMoveAnchorTo, onComplete: mockedOnComplete, pivot, position });

        const anchor = screen.getByLabelText('rotate anchor');
        fireEvent.pointerDown(anchor);
        fireEvent.pointerMove(anchor, { clientX: pivot.x, clientY: pivot.y });

        expect(mockedOnComplete).not.toHaveBeenCalled();
        expect(mockedOnMoveAnchorTo).toHaveBeenCalledWith(180);
    });

    it('calls onComplete when the interaction is completed', () => {
        const pivot = { x: 15, y: 15 };
        const position = { x: 10, y: 10 };
        const mockedOnComplete = jest.fn();
        const mockedOnMoveAnchorTo = jest.fn();
        renderApp({ onMoveAnchorTo: mockedOnMoveAnchorTo, onComplete: mockedOnComplete, pivot, position });

        const anchor = screen.getByLabelText('rotate anchor');
        fireEvent.pointerDown(anchor);
        fireEvent.pointerMove(anchor, { clientX: 15, clientY: -5 });
        fireEvent.pointerUp(anchor);

        expect(mockedOnMoveAnchorTo).toHaveBeenCalledWith(90);
        expect(mockedOnComplete).toHaveBeenCalled();
    });
});
