// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Polygon } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../../test-utils/utils';
import { ProjectProvider } from '../../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { AnnotatorContextMenuProvider } from '../../../providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { TaskProvider } from '../../../providers/task-provider/task-provider.component';
import { removeOffLimitPointsPolygon } from '../../geometry-utils';
import { EditPolygon as EditPolygonTool } from './edit-polygon.component';

const mockROI = getMockedROI({ x: 0, y: 0, width: 1000, height: 1000 });
const mockImage = getMockedImage(mockROI);

jest.mock('../../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    useAnnotationScene: () => ({ hasShapePointSelected: { current: false } }),
}));

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../geometry-utils', () => ({
    ...jest.requireActual('../../geometry-utils'),
    removeOffLimitPointsPolygon: jest.fn((shape) => shape),
}));

jest.mock('./../../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } }, setIsZoomDisabled: jest.fn() })),
}));

interface Point {
    x: number;
    y: number;
}

const moveLine = (rect: HTMLElement, startPoint: Point, endPoint: Point) => {
    fireEvent.pointerDown(rect, {
        buttons: 1,
        clientX: startPoint.x,
        clientY: startPoint.y,
    });

    fireEvent.pointerMove(rect, {
        buttons: 1,
        clientX: endPoint.x,
        clientY: endPoint.y,
    });

    fireEvent.pointerUp(rect, {
        buttons: 1,
        clientX: endPoint.x,
        clientY: endPoint.y,
    });
};

const renderApp = async (
    annotationToolContext: AnnotationToolContext,
    annotation: Annotation & {
        shape: {
            shapeType: ShapeType.Polygon;
        };
    }
) => {
    const result = render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <AnnotatorContextMenuProvider>
                    <EditPolygonTool annotationToolContext={annotationToolContext} annotation={annotation} />
                </AnnotatorContextMenuProvider>
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    return result;
};

describe('EditPolygonTool', () => {
    const annotation = getMockedAnnotation({
        id: 'polygon-1',
        shape: {
            shapeType: ShapeType.Polygon,
            points: [
                { x: 20, y: 10 },
                { x: 70, y: 30 },
                { x: 80, y: 90 },
            ],
        },
    }) as Annotation & { shape: Polygon };
    const shape = annotation.shape;

    const annotationToolContext = fakeAnnotationToolContext({
        annotations: [annotation],
    });
    const onComplete = annotationToolContext.scene.updateAnnotation;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('allows the user to translate a polygon', async () => {
        await renderApp(annotationToolContext, annotation);

        // Move the shape
        const startPoint = { x: 90, y: 10 };
        const endPoint = { x: 80, y: 0 };

        const rect = screen.getByLabelText('Drag to move shape');
        moveLine(rect, startPoint, endPoint);
        const translate = {
            x: startPoint.x - endPoint.x,
            y: startPoint.y - endPoint.y,
        };

        const finalShape = {
            ...shape,
            points: shape.points.map((point) => ({
                x: point.x - translate.x,
                y: point.y - translate.y,
            })),
        };

        expect(removeOffLimitPointsPolygon).toHaveBeenCalledWith(finalShape, mockROI);
        expect(onComplete).toHaveBeenCalledWith({
            ...annotation,
            shape: finalShape,
        });
    });

    it("allows the user to move one of the polygon's anchor points", async () => {
        const startPoint = { x: 70, y: 30 };
        const translate = { x: 10, y: 10 };

        const endPoint = {
            x: startPoint.x + translate.x,
            y: startPoint.y + translate.y,
        };

        await renderApp(annotationToolContext, annotation);

        const rect = screen.getByLabelText('Resize polygon 1 anchor');
        moveLine(rect, startPoint, endPoint);

        const finalShape = {
            ...shape,
            points: [
                { x: 20, y: 10 },
                { x: 80, y: 40 },
                { x: 80, y: 90 },
            ],
        };
        expect(removeOffLimitPointsPolygon).toHaveBeenCalledWith(finalShape, mockROI);
        expect(onComplete).toHaveBeenCalledWith({
            ...annotation,
            shape: finalShape,
        });
    });

    describe('adding a point to an existing polygon', () => {
        const mockAnnotation = getMockedAnnotation({
            id: 'polygon-1',
            shape: {
                shapeType: ShapeType.Polygon,
                points: [
                    { x: 10, y: 10 },
                    { x: 50, y: 50 },
                    { x: 10, y: 50 },
                ],
            },
        }) as Annotation & { shape: Polygon };
        const mockShape = mockAnnotation.shape;

        const hoverPoint = { clientX: 40, clientY: 50 };

        it('can add a point between two lines', async () => {
            const expectedProjectedPoint = { x: 45, y: 45 };

            await renderApp(annotationToolContext, mockAnnotation);

            const line = screen.getByLabelText('Line between point 0 and 1');
            fireEvent.pointerMove(line, { ...hoverPoint });

            const ghostPoint = screen.getByLabelText('Add a point between point 0 and 1');
            fireEvent.pointerDown(ghostPoint, { buttons: 1, ...hoverPoint });
            fireEvent.pointerUp(ghostPoint, { buttons: 1, ...hoverPoint });

            const finalShape = {
                ...mockShape,
                points: [mockShape.points[0], expectedProjectedPoint, mockShape.points[1], mockShape.points[2]],
            };
            expect(removeOffLimitPointsPolygon).not.toHaveBeenCalled();
            expect(onComplete).toHaveBeenCalledWith({
                ...mockAnnotation,
                shape: finalShape,
            });
        });

        it('can move the new point before adding it', async () => {
            const expectedProjectedPoint = { x: 45, y: 45 };
            const moveBy = { x: 5, y: 15 };

            await renderApp(annotationToolContext, mockAnnotation);

            const line = screen.getByLabelText('Line between point 0 and 1');
            fireEvent.pointerMove(line, { ...hoverPoint });

            const ghostPoint = screen.getByLabelText('Add a point between point 0 and 1');
            fireEvent.pointerDown(ghostPoint, { buttons: 1, ...hoverPoint });
            fireEvent.pointerMove(ghostPoint, {
                clientX: hoverPoint.clientX + moveBy.x,
                clientY: hoverPoint.clientY + moveBy.y,
            });
            fireEvent.pointerUp(ghostPoint, { buttons: 1, ...hoverPoint });

            const finalShape = {
                ...shape,
                points: [
                    mockShape.points[0],
                    {
                        x: expectedProjectedPoint.x + moveBy.x,
                        y: expectedProjectedPoint.y + moveBy.y,
                    },
                    mockShape.points[1],
                    mockShape.points[2],
                ],
            };
            expect(removeOffLimitPointsPolygon).toHaveBeenCalled();
            expect(onComplete).toHaveBeenCalledWith({
                ...mockAnnotation,
                shape: finalShape,
            });
        });
    });

    describe('removing points from a polygon', () => {
        const mockAnnotation = getMockedAnnotation({
            id: 'polygon-1',
            shape: {
                shapeType: ShapeType.Polygon,
                points: [
                    { x: 10, y: 10 },
                    { x: 30, y: 10 },
                    { x: 50, y: 30 },
                    { x: 50, y: 50 },
                    { x: 10, y: 50 },
                ],
            },
        }) as Annotation & { shape: Polygon };
        const mockShape = mockAnnotation.shape;

        it('removes a point from a polygon', async () => {
            await renderApp(annotationToolContext, mockAnnotation);

            const pointToRemove = screen.getByLabelText('Click to select point 0');
            fireEvent.click(pointToRemove);

            expect(pointToRemove).toHaveAttribute('aria-selected', 'true');
            await userEvent.keyboard('{Delete}');

            const finalShape = {
                ...mockShape,
                points: [mockShape.points[1], mockShape.points[2], mockShape.points[3], mockShape.points[4]],
            };
            expect(removeOffLimitPointsPolygon).toHaveBeenCalledWith(finalShape, mockROI);
            expect(onComplete).toHaveBeenCalledWith({
                ...mockAnnotation,
                shape: finalShape,
            });

            expect(pointToRemove).toHaveAttribute('aria-selected', 'false');
        });

        it('deselects points', async () => {
            await renderApp(annotationToolContext, mockAnnotation);

            const pointToRemove0 = screen.getByLabelText('Click to select point 0');
            const pointToRemove1 = screen.getByLabelText('Click to select point 1');
            const pointToRemove2 = screen.getByLabelText('Click to select point 2');

            fireEvent.click(pointToRemove0);
            expect(pointToRemove0).toHaveAttribute('aria-selected', 'true');

            fireEvent.click(pointToRemove1);
            expect(pointToRemove0).toHaveAttribute('aria-selected', 'false');
            expect(pointToRemove1).toHaveAttribute('aria-selected', 'true');

            fireEvent.click(pointToRemove0, { shiftKey: true });
            fireEvent.click(pointToRemove1, { shiftKey: true });
            fireEvent.click(pointToRemove2, { shiftKey: true });

            expect(pointToRemove0).toHaveAttribute('aria-selected', 'true');
            expect(pointToRemove1).toHaveAttribute('aria-selected', 'false');
            expect(pointToRemove2).toHaveAttribute('aria-selected', 'true');

            expect(pointToRemove0).toHaveAttribute('aria-selected', 'true');
            await userEvent.keyboard('{Delete}');

            const finalShape = {
                ...mockShape,
                points: [mockShape.points[1], mockShape.points[3], mockShape.points[4]],
            };
            expect(removeOffLimitPointsPolygon).toHaveBeenCalledWith(finalShape, mockROI);
            expect(onComplete).toHaveBeenCalledWith({
                ...mockAnnotation,
                shape: finalShape,
            });
        });

        it('removes the polygon if it ends up with 2 points or less', async () => {
            await renderApp(annotationToolContext, annotation);

            const pointToRemove = screen.getByLabelText('Click to select point 0');
            fireEvent.click(pointToRemove);
            expect(pointToRemove).toHaveAttribute('aria-selected', 'true');

            const otherPointToRemove = screen.getByLabelText('Shift click to select point 1');
            fireEvent.click(otherPointToRemove, { shiftKey: true });
            expect(otherPointToRemove).toHaveAttribute('aria-selected', 'true');

            fireEvent.click(screen.getByLabelText('Shift click to select point 2'), { shiftKey: true });

            await userEvent.keyboard('{Delete}');

            expect(annotationToolContext.scene.removeAnnotations).toBeCalled();
        });

        it('removes the polygon with the context menu option "delete"', async () => {
            await renderApp(annotationToolContext, mockAnnotation);

            const pointToRemove = screen.getByLabelText('Resize polygon 2 anchor');

            fireEvent.contextMenu(pointToRemove);

            const deleteOption = screen.getByText('Delete');
            fireEvent.click(deleteOption);

            const finalShape = {
                ...mockShape,
                points: [mockShape.points[0], mockShape.points[1], mockShape.points[3], mockShape.points[4]],
            };
            expect(removeOffLimitPointsPolygon).toHaveBeenCalledWith(finalShape, mockROI);
            expect(onComplete).toHaveBeenCalledWith({
                ...mockAnnotation,
                shape: finalShape,
            });
        });
    });
});
