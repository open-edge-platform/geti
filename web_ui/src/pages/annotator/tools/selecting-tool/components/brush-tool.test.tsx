// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

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
import { TaskProvider } from '../../../providers/task-provider/task-provider.component';
import { calculatePolygonArea, shapeToTurfPolygon } from '../../geometry-utils';
import { BrushTool } from './brush-tool.component';

const mockROI = getMockedROI();
const mockImage = getMockedImage(mockROI);

jest.mock('../../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../../providers/task-chain-provider/task-chain-provider.component', () => {
    const actual = jest.requireActual('../../../providers/task-chain-provider/task-chain-provider.component');
    return {
        ...actual,
        useTaskChain: jest.fn(() => ({ inputs: [] })),
    };
});

jest.mock('./../../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

const polygonAnnotation: Annotation = {
    id: 'test-polygon',
    labels: [],
    shape: {
        shapeType: ShapeType.Polygon,
        points: [
            { x: 0, y: 0 },
            { x: 10, y: 0 },
            { x: 10, y: 10 },
            { x: 0, y: 10 },
        ],
    },
    zIndex: 0,
    isSelected: true,
    isHidden: false,
    isLocked: false,
};
const circleAnnotation = getMockedAnnotation({}, ShapeType.Circle);
const rectAnnotation = getMockedAnnotation({}, ShapeType.Rect);

const renderApp = async (annotationToolContext: AnnotationToolContext, brushSize = 10, showCirclePreview = false) => {
    const result = render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
            <TaskProvider>
                <BrushTool
                    brushSize={brushSize}
                    showCirclePreview={showCirclePreview}
                    annotationToolContext={annotationToolContext}
                />
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    return result;
};

describe('BrushTool', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });
    const annotationToolContext = fakeAnnotationToolContext({
        annotations: [polygonAnnotation, circleAnnotation, rectAnnotation],
    });

    const movePointer = (container: SVGElement, moveTo: number, { x, y }: { x: number; y: number }) => {
        Array.from({ length: moveTo }).forEach((_, index) => {
            fireEvent.pointerMove(container, { clientX: x + index, clientY: y });
        });
    };

    const expectShowGhostAndHideAnnotation = () => {
        expect(screen.queryByLabelText('ghostPolygon')).toBeInTheDocument();
        expect(annotationToolContext.scene.replaceAnnotations).toHaveBeenCalledWith(expect.any(Array), true);
    };

    it('shape increases its size when the user clicks inside and moves the cursor', async () => {
        const spyUpdateAnnotation = annotationToolContext.scene.updateAnnotation as jest.Mock;
        const { container } = await renderApp(annotationToolContext);

        const testPolygon = polygonAnnotation.shape as Polygon;
        const lastPoint = testPolygon.points[testPolygon.points.length - 1];
        const svgContainer = container.querySelector('svg') as SVGElement;
        const iniPoint = { x: lastPoint.x + 1, y: lastPoint.y - 1 };

        fireEvent.pointerDown(svgContainer, { clientX: iniPoint.x, clientY: iniPoint.y });
        movePointer(svgContainer, 40, iniPoint);

        expectShowGhostAndHideAnnotation();

        fireEvent.pointerUp(svgContainer);

        expect(spyUpdateAnnotation).toHaveBeenLastCalledWith(
            expect.objectContaining({
                isHidden: false,
            })
        );
        expect(screen.queryByLabelText('ghostPolygon')).not.toBeInTheDocument();

        const newPolygon = (spyUpdateAnnotation.mock.calls[0][0] as Annotation).shape;

        expect(calculatePolygonArea(shapeToTurfPolygon(newPolygon))).toBeGreaterThan(
            calculatePolygonArea(shapeToTurfPolygon(testPolygon))
        );
    });

    it('shape decreases its size when the user clicks outside and touches the polygon', async () => {
        const spyUpdateAnnotation = annotationToolContext.scene.updateAnnotation as jest.Mock;
        const brushSize = 3;

        const { container } = await renderApp(annotationToolContext, brushSize);

        const testPolygon = polygonAnnotation.shape as Polygon;
        const lastPoint = testPolygon.points[testPolygon.points.length - 1];
        const svgContainer = container.querySelector('svg') as SVGElement;
        const iniPoint = { x: -lastPoint.x, y: lastPoint.y };

        fireEvent.pointerDown(svgContainer, { clientX: iniPoint.x, clientY: iniPoint.y });
        movePointer(svgContainer, 40, iniPoint);
        expectShowGhostAndHideAnnotation();

        fireEvent.pointerUp(svgContainer);

        expect(spyUpdateAnnotation).toHaveBeenLastCalledWith(
            expect.objectContaining({
                isHidden: false,
            })
        );
        expect(screen.queryByLabelText('ghostPolygon')).not.toBeInTheDocument();

        const newPolygon = (spyUpdateAnnotation.mock.calls[0][0] as Annotation).shape;

        expect(calculatePolygonArea(shapeToTurfPolygon(testPolygon))).toBeGreaterThan(
            calculatePolygonArea(shapeToTurfPolygon(newPolygon))
        );
    });
});
