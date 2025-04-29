// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen } from '@testing-library/react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { getMockedImage, getMockedROI } from '../../../../../test-utils/utils';
import { ProjectProvider } from '../../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { TaskProvider } from '../../../providers/task-provider/task-provider.component';
import { ANCHOR_SIZE } from '../resize-anchor.component';
import { EditBoundingBox as EditBoundingBoxTool } from './edit-bounding-box.component';

const mockROI = getMockedROI({ x: 0, y: 0, width: 1000, height: 1000 });
const mockImage = getMockedImage(mockROI);

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('./../../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 2.0, translation: { x: 0, y: 0 } } })),
}));

const renderApp = async (
    annotationToolContext: AnnotationToolContext,
    annotation: Annotation & {
        shape: {
            shapeType: ShapeType.Rect;
        };
    }
) => {
    const result = await render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <EditBoundingBoxTool annotationToolContext={annotationToolContext} annotation={annotation} />
            </TaskProvider>
        </ProjectProvider>
    );

    return result;
};

describe('EditRectangleTool', (): void => {
    const annotation = {
        id: 'rect-1',
        labels: [],
        shape: { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 300, height: 200 },
        zIndex: 0,
        isHovered: false,
        isSelected: false,
        isHidden: false,
        isLocked: false,
    };
    const shape = annotation.shape;

    const zoom = 2.0;
    const annotationToolContext = fakeAnnotationToolContext({
        annotations: [annotation],
        zoom,
    });
    const onComplete = annotationToolContext.scene.updateAnnotation;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('allows the user to translate a rectangle', async (): Promise<void> => {
        await renderApp(annotationToolContext, annotation);

        // Move the shape
        const startPoint = { x: 90, y: 10 };
        const endPoint = { x: 80, y: 0 };

        const rect = screen.getByLabelText('Drag to move shape');
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

        const translate = {
            x: (startPoint.x - endPoint.x) / zoom,
            y: (startPoint.y - endPoint.y) / zoom,
        };

        expect(onComplete).toBeCalledWith({
            ...annotation,
            shape: {
                ...shape,
                x: shape.x - translate.x,
                y: shape.y - translate.y,
            },
        });
    });

    it('does not allows the user to translate a rectangle outside the roi', async (): Promise<void> => {
        const iRoi = { x: 100, y: 100, width: 100, height: 100 };
        const iAnnotationToolContext = fakeAnnotationToolContext();

        const iAnnotation = {
            id: 'rect-1',
            labels: [],
            shape: {
                shapeType: ShapeType.Rect as const,
                x: iRoi.x,
                y: iRoi.y,
                width: iRoi.width / 2,
                height: iRoi.height / 2,
            },
            zIndex: 0,
            isHovered: false,
            isSelected: false,
            isHidden: false,
            isLocked: false,
        };

        jest.mocked(useROI).mockReturnValueOnce({ roi: iRoi, image: getMockedImage(iRoi) });

        await renderApp(iAnnotationToolContext, iAnnotation);
        // Move the shape
        const startPoint = { x: iAnnotation.shape.x, y: iAnnotation.shape.y };
        const endPoint = { x: 0, y: startPoint.y };

        const rect = screen.getByLabelText('Drag to move shape');
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

        expect(iAnnotationToolContext.scene.updateAnnotation).toBeCalledWith(iAnnotation);
    });

    test.each([
        [
            { x: shape.x, y: shape.y },
            { x: -10, y: -10 },
            { x: 0, y: 0 },
        ],
        [
            { x: shape.x, y: shape.y },
            { x: -10, y: mockROI.height + 10 },
            { x: 0, y: mockROI.height - shape.height },
        ],
        [
            { x: shape.x, y: shape.y },
            { x: mockROI.width + 10, y: mockROI.height + 10 },
            { x: mockROI.width - shape.width, y: mockROI.height - shape.height },
        ],
        [
            { x: shape.x, y: shape.y },
            { x: mockROI.width + 10, y: -10 },
            { x: mockROI.width - shape.width, y: 0 },
        ],
    ])(
        'keeps the bounding box in bounds of the roi when moving from %o to %o',
        async (startPoint, endPoint, expectedEndPoint) => {
            await renderApp(annotationToolContext, annotation);

            const rect = screen.getByLabelText('Drag to move shape');

            fireEvent.pointerDown(rect, {
                buttons: 1,
                clientX: zoom * startPoint.x,
                clientY: zoom * startPoint.y,
            });

            fireEvent.pointerMove(rect, {
                buttons: 1,
                clientX: zoom * endPoint.x,
                clientY: zoom * endPoint.y,
            });
            fireEvent.pointerUp(rect, {
                buttons: 1,
                clientX: zoom * endPoint.x,
                clientY: zoom * endPoint.y,
            });

            expect(onComplete).toBeCalledWith({
                ...annotation,
                shape: { ...shape, ...expectedEndPoint },
            });
        }
    );

    // These test validate that the user can resize a rectangle by moving one of
    // its anchor points.
    // Specifically we test each anchor point twice: ones where we move away from
    // the rectangle and another time where we move into the rectangle
    test.each([
        [
            'North west',
            { x: shape.x, y: shape.y },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x + 10,
                y: shape.y + 10,
                width: shape.width - 10,
                height: shape.height - 10,
            },
        ],
        [
            'North west',
            { x: shape.x, y: shape.y },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x - 10,
                y: shape.y - 10,
                width: shape.width + 10,
                height: shape.height + 10,
            },
        ],
        [
            'North',
            { x: shape.x + shape.width / 2, y: shape.y },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y + 10,
                width: shape.width,
                height: shape.height - 10,
            },
        ],
        [
            'North',
            { x: shape.x, y: shape.y },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y - 10,
                width: shape.width,
                height: shape.height + 10,
            },
        ],
        [
            'North east',
            { x: shape.x + shape.width, y: shape.y },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y + 10,
                width: shape.width + 10,
                height: shape.height - 10,
            },
        ],
        [
            'North east',
            { x: shape.x + shape.width, y: shape.y },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y - 10,
                width: shape.width - 10,
                height: shape.height + 10,
            },
        ],
        [
            'East',
            { x: shape.x + shape.width, y: shape.y + shape.height / 2 },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width + 10,
                height: shape.height,
            },
        ],
        [
            'East',
            { x: shape.x + shape.width, y: shape.y + shape.height / 2 },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width - 10,
                height: shape.height,
            },
        ],
        [
            'South east',
            { x: shape.x + shape.width, y: shape.y + shape.height },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width + 10,
                height: shape.height + 10,
            },
        ],
        [
            'South east',
            { x: shape.x + shape.width, y: shape.y + shape.height },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width - 10,
                height: shape.height - 10,
            },
        ],
        [
            'South',
            { x: shape.x + shape.width / 2, y: shape.y + shape.height },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width,
                height: shape.height + 10,
            },
        ],
        [
            'South',
            { x: shape.x + shape.width / 2, y: shape.y + shape.height },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width,
                height: shape.height - 10,
            },
        ],
        [
            'South west',
            { x: shape.x, y: shape.y + shape.height },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x + 10,
                y: shape.y,
                width: shape.width - 10,
                height: shape.height + 10,
            },
        ],
        [
            'South west',
            { x: shape.x, y: shape.y + shape.height },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x - 10,
                y: shape.y,
                width: shape.width + 10,
                height: shape.height - 10,
            },
        ],
        [
            'West',
            { x: shape.x, y: shape.y + shape.height / 2 },
            { x: 10, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x + 10,
                y: shape.y,
                width: shape.width - 10,
                height: shape.height,
            },
        ],
        [
            'West',
            { x: shape.x, y: shape.y + shape.height / 2 },
            { x: -10, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x - 10,
                y: shape.y,
                width: shape.width + 10,
                height: shape.height,
            },
        ],
        // Test that the bounding box isn't allowed to be moved outside of the canvas
        [
            'North west',
            { x: shape.x, y: shape.y },
            { x: -20, y: -20 },
            {
                shapeType: ShapeType.Rect,
                x: 0,
                y: 0,
                width: shape.width + shape.x,
                height: shape.height + shape.y,
            },
        ],
        [
            'North',
            { x: shape.x + shape.width / 2, y: shape.y },
            { x: 10, y: -20 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: 0,
                width: shape.width,
                height: shape.height + shape.y,
            },
        ],
        [
            'North east',
            { x: shape.x + shape.width, y: shape.y },
            { x: mockROI.width, y: -10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: 0,
                width: mockROI.width - shape.x,
                height: shape.height + shape.y,
            },
        ],
        [
            'East',
            { x: shape.x + shape.width, y: shape.y + shape.height / 2 },
            { x: mockROI.width, y: 10 },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: mockROI.width - shape.x,
                height: shape.height,
            },
        ],
        [
            'South east',
            { x: shape.x + shape.width, y: shape.y + shape.height },
            { x: mockROI.width, y: mockROI.height },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: mockROI.width - shape.x,
                height: mockROI.height - shape.y,
            },
        ],
        [
            'South',
            { x: shape.x + shape.width / 2, y: shape.y + shape.height },
            { x: 10, y: mockROI.height },
            {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width,
                height: mockROI.height - shape.y,
            },
        ],
        [
            'South west',
            { x: shape.x, y: shape.y + shape.height },
            { x: -mockROI.width, y: mockROI.height },
            {
                shapeType: ShapeType.Rect,
                x: 0,
                y: shape.y,
                width: shape.width + shape.x,
                height: mockROI.height - shape.y,
            },
        ],
        [
            'West',
            { x: shape.x, y: shape.y + shape.height / 2 },
            { x: -mockROI.width, y: mockROI.height },
            {
                shapeType: ShapeType.Rect,
                x: 0,
                y: shape.y,
                width: shape.width + shape.x,
                height: shape.height,
            },
        ],
    ])('Translate using %s anchor from %o by %o', async (anchor, startPoint, translate, expectedRect) => {
        const endPoint = {
            x: startPoint.x + translate.x * zoom,
            y: startPoint.y + translate.y * zoom,
        };

        await renderApp(annotationToolContext, annotation);

        const rect = screen.getByLabelText(`${anchor} resize anchor`);

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

        expect(onComplete).toBeCalledWith({ ...annotation, shape: expectedRect });
    });

    describe('Resizing to its minimum', () => {
        it('leaves a gap between anchor points', async () => {
            const gap = (2 * ANCHOR_SIZE) / zoom;
            const startPoint = { x: shape.x, y: shape.y };
            const expectedRect = {
                shapeType: ShapeType.Rect,
                x: shape.x + shape.width - gap,
                y: shape.y + shape.height - gap,
                width: gap,
                height: gap,
            };

            const endPoint = {
                x: startPoint.x + shape.width * zoom,
                y: startPoint.y + shape.height * zoom,
            };

            await renderApp(annotationToolContext, annotation);

            const rect = screen.getByLabelText(`North west resize anchor`);
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

            expect(onComplete).toBeCalledWith({ ...annotation, shape: expectedRect });
        });
    });
});
