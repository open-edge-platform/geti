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

import { act, render, screen } from '@testing-library/react';

import '@testing-library/jest-dom/extend-expect';

import { MIN_POINTS_MESSAGE } from '../../utils';
import { EMPTY_POINT_MESSAGE } from './empty-point-message.component';
import { PoseTemplate, PoseTemplateProps } from './pose-template.component';

const addPoint = (mouseEventInit: MouseEventInit) => {
    const drawingBox = screen.getByLabelText('drawing box');
    const pointerupEvent = new MouseEvent('pointerup', { ...mouseEventInit, bubbles: true, cancelable: true });

    act(() => {
        drawingBox.dispatchEvent(pointerupEvent);
    });
};

describe('PoseTemplate', () => {
    const renderApp = ({
        animationDirection = 0,
        setValidationError = jest.fn(),
        updateProjectState = jest.fn(),
        keypointError,
    }: Partial<PoseTemplateProps>) => {
        render(
            <PoseTemplate
                keypointError={keypointError}
                animationDirection={animationDirection}
                setValidationError={setValidationError}
                updateProjectState={updateProjectState}
            />
        );
    };

    beforeEach(() => {
        SVGElement.prototype.releasePointerCapture = jest.fn();
    });

    describe('error messages', () => {
        it('message is visible', () => {
            renderApp({ keypointError: MIN_POINTS_MESSAGE });

            expect(screen.getByTestId('info-section')).toBeInTheDocument();
            expect(screen.getByText(MIN_POINTS_MESSAGE)).toBeInTheDocument();
        });
    });

    it('updates projectTypeMetadata after state updates', async () => {
        const mockUpdateProjectState = jest.fn();
        renderApp({ updateProjectState: mockUpdateProjectState });

        addPoint({ clientX: 100, clientY: 100 });

        expect(mockUpdateProjectState).toHaveBeenLastCalledWith({
            projectTypeMetadata: [
                expect.objectContaining({
                    labels: expect.arrayContaining([expect.objectContaining({ name: '1' })]),
                    keypointStructure: {
                        edges: [],
                        positions: [{ label: '1', x: 0.1, y: 0.1 }],
                    },
                }),
            ],
        });
    });

    it('add points message is not visible when there are points', async () => {
        renderApp({});

        expect(screen.queryByText(EMPTY_POINT_MESSAGE)).toBeInTheDocument();

        addPoint({ clientX: 150, clientY: 75 });

        expect(screen.queryByText(EMPTY_POINT_MESSAGE)).not.toBeInTheDocument();
    });
});
