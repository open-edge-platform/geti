// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act } from 'react';

import { fireEvent, screen } from '@testing-library/react';

import { Point } from '../../../../../core/annotations/shapes.interface';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { annotatorRender as render } from '../../../../annotator/test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../../annotator/zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../../annotator/zoom/zoom-provider.component';
import { HiddenEdge, HiddenEdgeProps } from './hidden-edge.component';

const movePoint = (element: HTMLElement, newPoint: Point) => {
    act(() => {
        element.dispatchEvent(
            new MouseEvent('pointermove', {
                bubbles: true,
                cancelable: true,
                clientX: newPoint.x,
                clientY: newPoint.y,
            })
        );
    });
};

describe('Edge', () => {
    const toLine = getMockedKeypointNode({ label: getMockedLabel({ color: 'green', name: '1' }), x: 60, y: 10 });
    const fromLine = getMockedKeypointNode({ label: getMockedLabel({ color: 'green', name: '2' }), x: 10, y: 10 });

    const renderApp = async ({
        to = getMockedKeypointNode({ label: getMockedLabel({ color: 'green' }) }),
        from = getMockedKeypointNode({ label: getMockedLabel({ color: 'blue' }) }),
        onSelect = jest.fn(),
        onNewIntermediatePoint = jest.fn(),
        isSelected = false,
        isHovered = false,
    }: Partial<HiddenEdgeProps>) => {
        await render(
            <ZoomProvider>
                <TransformZoomAnnotation>
                    <svg width='500' height='500'>
                        <HiddenEdge
                            to={to}
                            from={from}
                            isHovered={isHovered}
                            isSelected={isSelected}
                            onSelect={onSelect}
                            onNewIntermediatePoint={onNewIntermediatePoint}
                        />
                    </svg>
                </TransformZoomAnnotation>
            </ZoomProvider>
        );
    };

    it('calls onSelect when the edge is not selected and receives a click', async () => {
        const mockedOnSelect = jest.fn();
        const mockedOnNewIntermediatePoint = jest.fn();
        await renderApp({
            isSelected: false,
            from: fromLine,
            to: toLine,
            onSelect: mockedOnSelect,
            onNewIntermediatePoint: mockedOnNewIntermediatePoint,
        });

        fireEvent.click(screen.getByLabelText(`hidden padded edge ${fromLine.label.name} - ${toLine.label.name}`));

        expect(mockedOnSelect).toHaveBeenCalledWith(false);
        expect(mockedOnNewIntermediatePoint).not.toHaveBeenCalled();
    });

    it('calls onNewIntermediatePoint after creating a ghost point', async () => {
        const mockedOnSelect = jest.fn();
        const mockedOnNewIntermediatePoint = jest.fn();
        await renderApp({
            to: toLine,
            from: fromLine,
            isHovered: true,
            isSelected: true,
            onSelect: mockedOnSelect,
            onNewIntermediatePoint: mockedOnNewIntermediatePoint,
        });
        const ghostPoint = { x: 20, y: 10 };
        const line = screen.getByLabelText(`hidden padded edge ${fromLine.label.name} - ${toLine.label.name}`);

        movePoint(line, ghostPoint);
        expect(screen.getByLabelText('ghost keypoint')).toBeVisible();

        fireEvent.click(line);
        expect(mockedOnSelect).not.toHaveBeenCalled();
        expect(mockedOnNewIntermediatePoint).toHaveBeenCalledWith(ghostPoint, fromLine, toLine);
    });
});
