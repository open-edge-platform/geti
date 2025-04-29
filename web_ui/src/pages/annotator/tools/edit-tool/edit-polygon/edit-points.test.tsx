// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { ReactNode } from 'react';

import { fireEvent, render, screen } from '@testing-library/react';

import { Polygon } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { KeyMap } from '../../../../../shared/keyboard-events/keyboard.interface';
import { ThemeProvider } from '../../../../../theme/theme-provider.component';
import { AnnotatorContextMenuProvider } from '../../../providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { EditPoints } from './edit-points.component';

const roi = { x: 0, y: 0, width: 1000, height: 1000 };

jest.mock('../../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    useAnnotationScene: () => ({ hasShapePointSelected: { current: false } }),
}));

jest.mock('../../../zoom/zoom-provider.component', () => ({
    useZoom: () => ({ setIsZoomDisabled: jest.fn() }),
}));

const renderEditPoints = (element: ReactNode) => {
    render(
        <ThemeProvider>
            <AnnotatorContextMenuProvider>
                <svg>{element}</svg>
            </AnnotatorContextMenuProvider>
        </ThemeProvider>
    );
};

describe('EditPoints', () => {
    const polygon: Polygon = {
        shapeType: ShapeType.Polygon,
        points: [
            { x: 20, y: 10 },
            { x: 70, y: 30 },
            { x: 80, y: 90 },
        ],
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterAll(() => {
        jest.clearAllMocks();
    });

    it('deletes a single point', async () => {
        const mockRemovePoints = jest.fn();

        renderEditPoints(
            <EditPoints
                roi={roi}
                zoom={1}
                shape={polygon}
                addPoint={jest.fn()}
                onComplete={jest.fn()}
                moveAnchorTo={jest.fn()}
                removePoints={mockRemovePoints}
            />
        );

        const pointIndex = 0;
        const point = screen.getByLabelText(`Click to select point ${pointIndex}`);
        expect(point).toHaveAttribute('aria-selected', 'false');

        fireEvent.click(point);

        expect(point).toHaveAttribute('aria-selected', 'true');

        fireEvent.keyDown(document.body, { key: 'Delete', keyCode: 46, code: KeyMap.Delete });
        expect(mockRemovePoints).toHaveBeenLastCalledWith([pointIndex]);
    });

    it('selects and deletes multiple points', async () => {
        const mockRemovePoints = jest.fn();

        renderEditPoints(
            <EditPoints
                roi={roi}
                zoom={1}
                shape={polygon}
                addPoint={jest.fn()}
                onComplete={jest.fn()}
                moveAnchorTo={jest.fn()}
                removePoints={mockRemovePoints}
            />
        );
        const pointOneIndex = 0;
        const pointTwoIndex = 1;
        const pointOne = screen.getByLabelText(`Click to select point ${pointOneIndex}`);
        const pointTwo = screen.getByLabelText(`Click to select point ${pointTwoIndex}`);
        expect(pointOne).toHaveAttribute('aria-selected', 'false');
        expect(pointTwo).toHaveAttribute('aria-selected', 'false');

        fireEvent.click(pointOne, { shiftKey: true });
        fireEvent.click(pointTwo, { shiftKey: true });

        expect(pointOne).toHaveAttribute('aria-selected', 'true');
        expect(pointTwo).toHaveAttribute('aria-selected', 'true');

        fireEvent.keyDown(document.body, { key: 'Delete', keyCode: 46, code: KeyMap.Delete });
        expect(mockRemovePoints).toHaveBeenLastCalledWith([pointOneIndex, pointTwoIndex]);
    });

    describe('context menu', () => {
        it('deletes a single point', async () => {
            const mockRemovePoints = jest.fn();

            renderEditPoints(
                <EditPoints
                    roi={roi}
                    zoom={1}
                    shape={polygon}
                    addPoint={jest.fn()}
                    onComplete={jest.fn()}
                    moveAnchorTo={jest.fn()}
                    removePoints={mockRemovePoints}
                />
            );

            const pointIndex = 2;
            const point = screen.getByLabelText(`Click to select point ${pointIndex}`);
            fireEvent.contextMenu(point);

            expect(point).toHaveAttribute('aria-selected', 'true');

            expect(screen.getByLabelText('Delete point')).toBeInTheDocument();
            fireEvent.click(screen.getByLabelText('Delete'));

            expect(mockRemovePoints).toHaveBeenLastCalledWith([pointIndex]);
        });

        it('selects and deletes multiple points', async () => {
            const mockRemovePoints = jest.fn();

            renderEditPoints(
                <EditPoints
                    roi={roi}
                    zoom={1}
                    shape={polygon}
                    addPoint={jest.fn()}
                    onComplete={jest.fn()}
                    moveAnchorTo={jest.fn()}
                    removePoints={mockRemovePoints}
                />
            );
            const pointOneIndex = 0;
            const pointTwoIndex = 1;
            const pointOne = screen.getByLabelText(`Click to select point ${pointOneIndex}`);
            const pointTwo = screen.getByLabelText(`Click to select point ${pointTwoIndex}`);

            expect(pointOne).toHaveAttribute('aria-selected', 'false');
            expect(pointTwo).toHaveAttribute('aria-selected', 'false');

            fireEvent.click(pointOne, { shiftKey: true });
            fireEvent.click(pointTwo, { shiftKey: true });
            fireEvent.contextMenu(pointTwo, { shiftKey: true });

            expect(pointOne).toHaveAttribute('aria-selected', 'true');
            expect(pointTwo).toHaveAttribute('aria-selected', 'true');

            fireEvent.click(screen.getByLabelText('Delete'));
            expect(mockRemovePoints).toHaveBeenLastCalledWith([pointOneIndex, pointTwoIndex]);
        });
    });
});
