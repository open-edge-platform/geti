// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Circle, Point } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../../../test-utils/utils';
import { ProjectProvider } from '../../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { TaskProvider } from '../../../providers/task-provider/task-provider.component';
import { getMaxCircleRadius } from '../../circle-tool/utils';
import { calculateAnchorPoint, EditCircle as EditCircleTool } from './edit-circle.component';

const mockROI = { x: 0, y: 0, width: 200, height: 200 };
const mockImage = getMockedImage(mockROI);

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('./../../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

const renderApp = async (
    annotation: Annotation & { shape: { shapeType: ShapeType.Circle } },
    annotationToolContext: AnnotationToolContext
) => {
    const result = render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <EditCircleTool annotationToolContext={annotationToolContext} annotation={annotation} />
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    return result;
};

describe('EditCircleTool', () => {
    const annotation = {
        id: 'circle-1',
        labels: [],
        shape: {
            shapeType: ShapeType.Circle,
            x: mockROI.width / 2,
            y: mockROI.height / 2,
            r: 20,
        } as Circle,
        zIndex: 0,
        isHovered: false,
        isSelected: false,
        isHidden: false,
        isLocked: false,
    };
    const shape = annotation.shape;
    const annotationToolContext = fakeAnnotationToolContext({
        annotations: [annotation],
    });
    const { updateAnnotation, removeAnnotations } = annotationToolContext.scene;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('allows the user to translate a circle', async () => {
        await renderApp(annotation, annotationToolContext);

        const startPoint = { x: 90, y: 10 };
        const endPoint = { x: 80, y: 0 };
        const rect = screen.getByLabelText('Drag to move shape');
        moveShape(rect, startPoint, endPoint);

        expect(updateAnnotation).toHaveBeenCalledWith({
            ...annotation,
            shape: {
                ...shape,
                x: shape.x + endPoint.x - startPoint.x,
                y: shape.y + endPoint.y - startPoint.y,
            },
        });
    });

    it('allows the user to resize a circle', async () => {
        const { container } = await renderApp(annotation, annotationToolContext);

        const startPoint = { x: shape.x + shape.r, y: shape.y };
        const endPoint = { x: shape.x + shape.r + 10, y: shape.y + 10 };
        const expectedRadius = Math.round(
            Math.sqrt(Math.pow(shape.x - endPoint.x, 2) + Math.pow(shape.y - endPoint.y, 2))
        );

        const newShape = { ...shape, r: expectedRadius };
        const angle = Math.atan2(shape.y - endPoint.y, shape.x - endPoint.x);
        const calculatedAnchorPoint = calculateAnchorPoint(newShape, angle, expectedRadius);

        const anchor = screen.getByLabelText('Resize circle anchor');
        // Move the resize anchor from its starting point
        moveShape(anchor, startPoint, endPoint);

        const movedAnchor = screen.getByLabelText('Resize circle anchor');
        const anchorPoint = {
            x: movedAnchor.getAttribute('cx'),
            y: movedAnchor.getAttribute('cy'),
        };

        expect(Number(anchorPoint.x)).toBeCloseTo(calculatedAnchorPoint.x);
        expect(Number(anchorPoint.y)).toBeCloseTo(calculatedAnchorPoint.y);

        // The line should start from the circle's origin and end at the anchor point
        const radiusLine = container.querySelector('line[stroke-dasharray]');

        expect(radiusLine).toHaveAttribute('x1', `${shape.x}`);
        expect(radiusLine).toHaveAttribute('y1', `${shape.y}`);
        expect(radiusLine).toHaveAttribute('x2', anchorPoint.x);
        expect(radiusLine).toHaveAttribute('y2', anchorPoint.y);

        expect(updateAnnotation).toHaveBeenCalledWith({
            ...annotation,
            shape: { ...shape, r: expectedRadius },
        });
    });

    it('allows user to resize circle to the min radius', async () => {
        await renderApp(annotation, annotationToolContext);

        const startPoint = { x: shape.x + shape.r, y: shape.y };
        const endPoint = { x: shape.x, y: shape.y };
        const expectedRadius = 1;

        const anchor = screen.getByLabelText('Resize circle anchor');
        moveShape(anchor, startPoint, endPoint);

        expect(updateAnnotation).toHaveBeenCalledWith({
            ...annotation,
            shape: { ...shape, r: expectedRadius },
        });
    });

    it('allows user to resize circle to the max radius', async () => {
        await renderApp(annotation, annotationToolContext);
        const maxRadius = getMaxCircleRadius(mockROI);

        const startPoint = { x: shape.x + shape.r, y: shape.y };
        const endPoint = { x: shape.x + shape.r + maxRadius, y: shape.y };
        const expectedRadius = maxRadius;

        const anchor = screen.getByLabelText('Resize circle anchor');
        moveShape(anchor, startPoint, endPoint);

        expect(updateAnnotation).toHaveBeenCalledWith({
            ...annotation,
            shape: { ...shape, r: expectedRadius },
        });
    });

    it('removes circle out of roi limits', async () => {
        await renderApp(annotation, annotationToolContext);

        const startPoint = { x: 0, y: 0 };
        const endPoint = { x: mockROI.width * 2, y: mockROI.height };
        const rect = screen.getByLabelText('Drag to move shape');
        moveShape(rect, startPoint, endPoint);

        expect(updateAnnotation).not.toHaveBeenCalled();
        expect(removeAnnotations).toHaveBeenCalledWith([
            {
                ...annotation,
                shape: {
                    ...shape,
                    x: 100,
                    y: 100,
                },
            },
        ]);
    });
});

const moveShape = (rect: HTMLElement, startPoint: Point, endPoint: Point) => {
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
