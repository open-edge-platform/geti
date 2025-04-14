// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { act, fireEvent, screen } from '@testing-library/react';

import '@testing-library/jest-dom/extend-expect';

import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { SelectedProvider } from '../../../../annotator/providers/selected-provider/selected-provider.component';
import { annotatorRender } from '../../../../annotator/test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../../annotator/zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../../annotator/zoom/zoom-provider.component';
import { CanvasTemplate, CanvasTemplateProps } from './canvas-template.component';

const addPoint = (mouseEventInit: MouseEventInit) => {
    const drawingBox = screen.queryByLabelText('drawing box');
    const pointerupEvent = new MouseEvent('pointerup', { ...mouseEventInit, bubbles: true, cancelable: true });

    act(() => {
        drawingBox && drawingBox.dispatchEvent(pointerupEvent);
    });
};

describe('CanvasTemplate', () => {
    const renderApp = async ({
        roi = { x: 0, y: 0, width: 100, height: 100 },
        state = { edges: [], points: [] },
        isAddPointEnabled = true,
        onStateUpdate = jest.fn(),
    }: Partial<CanvasTemplateProps>) => {
        await annotatorRender(
            <ZoomProvider>
                <TransformZoomAnnotation>
                    <SelectedProvider>
                        <CanvasTemplate
                            roi={roi}
                            state={state}
                            isAddPointEnabled={isAddPointEnabled}
                            onStateUpdate={onStateUpdate}
                            isLabelOptionsEnabled={false}
                        />
                    </SelectedProvider>
                </TransformZoomAnnotation>
            </ZoomProvider>
        );
    };

    beforeEach(() => {
        SVGElement.prototype.releasePointerCapture = jest.fn();
    });

    it('adds a new point', async () => {
        const mockedOnStateUpdate = jest.fn();
        await renderApp({ onStateUpdate: mockedOnStateUpdate });

        addPoint({ clientX: 0, clientY: 0 });

        expect(mockedOnStateUpdate).toHaveBeenCalledWith({
            edges: [],
            points: expect.arrayContaining([expect.objectContaining({ x: 0, y: 0 })]),
            skipHistory: false,
        });
    });

    it('does not add a point when adding is disabled', async () => {
        const mockedOnStateUpdate = jest.fn();
        await renderApp({ onStateUpdate: mockedOnStateUpdate, isAddPointEnabled: false });

        addPoint({ clientX: 0, clientY: 0 });

        expect(mockedOnStateUpdate).not.toHaveBeenCalled();
    });

    it('displays the closest labels based on pointer movement', async () => {
        const point1 = getMockedKeypointNode({
            label: getMockedLabel({ id: 'label-1', name: 'label-1' }),
            x: 10,
            y: 0,
        });
        const point2 = getMockedKeypointNode({
            label: getMockedLabel({ id: 'label-2', name: 'label-2' }),
            x: 20,
            y: 0,
        });

        await renderApp({
            state: {
                edges: [],
                points: [point1, point2],
            },
        });
        const container = screen.getByRole('editor');

        expect(screen.queryByTestId(`pose label - ${point1.label.name}`)).not.toBeInTheDocument();
        expect(screen.queryByTestId(`pose label - ${point2.label.name}`)).not.toBeInTheDocument();

        fireEvent.pointerMove(container, { clientX: point2.x + 2, clientY: 0 });
        expect(screen.queryByTestId(`pose label - ${point2.label.name}`)).toBeVisible();
        expect(screen.queryByTestId(`pose label - ${point1.label.name}`)).not.toBeInTheDocument();

        fireEvent.pointerMove(container, { clientX: point1.x - 2, clientY: 0 });
        expect(screen.queryByTestId(`pose label - ${point1.label.name}`)).toBeVisible();
        expect(screen.queryByTestId(`pose label - ${point2.label.name}`)).not.toBeInTheDocument();
    });
});
