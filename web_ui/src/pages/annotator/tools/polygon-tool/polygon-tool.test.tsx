// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { Point, Polygon } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useLoadAIWebworker } from '../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getMockedImage, getMockedROI } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationToolContext, ToolType } from '../../core/annotation-tool-context.interface';
import { useIntelligentScissors } from '../../hooks/use-intelligent-scissors.hook';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationToolProvider } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotator } from '../../providers/annotator-provider/annotator-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { PolygonStateProvider, usePolygonState } from './polygon-state-provider.component';
import { PolygonTool } from './polygon-tool.component';
import { PolygonMode } from './polygon-tool.enum';

jest.mock('../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-scene-provider/annotation-scene-provider.component'),
    useAnnotationScene: jest.fn(),
}));

jest.mock('../../providers/annotator-provider/annotator-provider.component', () => ({
    ...jest.requireActual('../../providers/annotator-provider/annotator-provider.component'),
    useAnnotator: jest.fn(),
}));

jest.mock('../../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(),
}));

jest.mock('lodash', () => ({
    ...jest.requireActual('lodash'),
    debounce: (callback: () => void) => callback,
}));

jest.mock('../../hooks/use-intelligent-scissors.hook', () => ({
    useIntelligentScissors: jest.fn(() => [jest.fn(), jest.fn(), jest.fn()]),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({ selectedTask: null, tasks: [], defaultLabel: null })),
}));

const mockROI = getMockedROI();
const mockImage = getMockedImage(mockROI);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

const mockOptimizePolygon = jest.fn((polygon) => polygon);
const mockOptimizeSegments = jest.fn((segments: Point[][]) => ({
    shapeType: ShapeType.Polygon,
    points: segments.flat(),
}));

jest.mock('../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook', () => {
    return {
        ...jest.requireActual('../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook'),
        useLoadAIWebworker: jest.fn(),
    };
});

const drawShape = async (): Promise<{ editor: HTMLElement; shape: Polygon }> => {
    const editor = await screen.findByRole('editor');

    fireEvent.pointerMove(editor, { clientX: 50, clientY: 50 });
    fireEvent.pointerDown(editor, { buttons: 1, clientX: 50, clientY: 50 });
    fireEvent.pointerUp(editor, { buttons: 1, clientX: 50, clientY: 50 });

    fireEvent.pointerMove(editor, { clientX: 10, clientY: 50 });
    fireEvent.pointerDown(editor, { buttons: 1, clientX: 10, clientY: 50 });

    fireEvent.pointerMove(editor, { clientX: 10, clientY: 10 });
    fireEvent.pointerDown(editor, { buttons: 1, clientX: 10, clientY: 10 });

    fireEvent.pointerMove(editor, { buttons: 1, clientX: 50, clientY: 10 });
    fireEvent.pointerDown(editor, { buttons: 1, clientX: 50, clientY: 10 });

    fireEvent.pointerMove(editor, { buttons: 1, clientX: 50, clientY: 50 });

    const shape: Polygon = {
        shapeType: ShapeType.Polygon,
        points: [
            { x: 50, y: 50 },
            { x: 10, y: 50 },
            { x: 10, y: 10 },
            { x: 50, y: 10 },
        ],
    };

    return { editor, shape };
};

const MagneticLassoPolygonTool = ({ annotationToolContext }: { annotationToolContext: AnnotationToolContext }) => {
    const { setMode } = usePolygonState();

    return (
        <>
            <button onClick={() => setMode(PolygonMode.MagneticLasso)}>change mode to MagneticLasso</button>
            <PolygonTool annotationToolContext={annotationToolContext} />
        </>
    );
};

const renderApp = async (annotationToolContext: AnnotationToolContext) => {
    const selectedMediaItem = {
        ...getMockedImageMediaItem({}),
        image: mockImage,
        annotations: annotationToolContext.scene.annotations,
    };

    jest.mocked(useAnnotationScene).mockReturnValue(annotationToolContext.scene);
    // @ts-expect-error We only care about active tool stuff
    jest.mocked(useAnnotator).mockReturnValue({ activeTool: ToolType.PolygonTool, setActiveTool: jest.fn() });
    // @ts-expect-error We only care about selectedMediaItem tool stuff
    jest.mocked(useSelectedMediaItem).mockReturnValue({ selectedMediaItem });
    jest.mocked(useLoadAIWebworker).mockImplementation(() => {
        return {
            worker: {
                optimizePolygon: mockOptimizePolygon,
                optimizeSegments: mockOptimizeSegments,
            },
        };
    });

    const result = render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <AnnotationToolProvider>
                    <PolygonStateProvider>
                        <PolygonTool annotationToolContext={annotationToolContext} />
                    </PolygonStateProvider>
                </AnnotationToolProvider>
            </TaskProvider>
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    return result;
};

describe('PolygonTool', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.mocked(useIntelligentScissors).mockClear();
    });

    it('draws a polygon with segments optimization', async () => {
        const annotationToolContext = fakeAnnotationToolContext();

        const onComplete = annotationToolContext.scene.addShapes;

        await renderApp(annotationToolContext);

        const { shape, editor } = await drawShape();
        fireEvent.pointerUp(editor, { buttons: 1, clientX: 50, clientY: 50 });

        await waitFor(() => expect(onComplete).toHaveBeenCalledWith([shape]));
        expect(mockOptimizeSegments).toHaveBeenCalledWith(shape.points.map((point) => [point]));
    });

    it('draws a polygon with polygon optimization', async (): Promise<void> => {
        const annotationToolContext = fakeAnnotationToolContext();
        const onComplete = annotationToolContext.scene.addShapes;

        const selectedMediaItem = {
            ...getMockedImageMediaItem({}),
            image: mockImage,
            annotations: annotationToolContext.scene.annotations,
        };

        jest.mocked(useIntelligentScissors).mockImplementation((data) => ({
            onPointerUp: () => data.complete(PolygonMode.MagneticLasso),
            onPointerDown: jest.fn(),
            onPointerMove: jest.fn(),
        }));

        jest.mocked(useAnnotationScene).mockReturnValue(annotationToolContext.scene);
        // @ts-expect-error We only care about active tool stuff
        jest.mocked(useAnnotator).mockReturnValue({ activeTool: ToolType.PolygonTool, setActiveTool: jest.fn() });
        // @ts-expect-error We only care about selectedMediaItem tool stuff
        jest.mocked(useSelectedMediaItem).mockReturnValue({ selectedMediaItem });

        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <TaskProvider>
                    <AnnotationToolProvider>
                        <PolygonStateProvider>
                            <MagneticLassoPolygonTool annotationToolContext={annotationToolContext} />
                        </PolygonStateProvider>
                    </AnnotationToolProvider>
                </TaskProvider>
            </ProjectProvider>
        );

        const { shape, editor } = await drawShape();
        fireEvent.click(screen.getByText('change mode to MagneticLasso'));
        fireEvent.pointerUp(editor, { buttons: 1, clientX: 50, clientY: 50 });

        await waitFor(() => expect(onComplete).toHaveBeenCalledWith([shape]));
        expect(mockOptimizePolygon).toHaveBeenCalledWith(shape);
    });

    it('cancels a polygon if the user did not provide additional points', async (): Promise<void> => {
        const annotationToolContext = fakeAnnotationToolContext();
        const onComplete = annotationToolContext.scene.addShapes;
        const { container } = await renderApp(annotationToolContext);

        const editor = await screen.findByRole('editor');
        fireEvent.pointerMove(editor, { clientX: 10, clientY: 10 });
        fireEvent.pointerDown(editor, { buttons: 1, clientX: 10, clientY: 10 });

        fireEvent.pointerMove(editor, { clientX: 11, clientY: 11 });
        fireEvent.pointerDown(editor, { buttons: 1, clientX: 11, clientY: 11 });
        fireEvent.pointerUp(editor, { buttons: 1, clientX: 11, clientY: 11 });

        expect(onComplete).not.toHaveBeenCalled();
        expect(container.querySelector('polygon')).toBeNull();
    });

    it('does not draw polygons outside the roi', async (): Promise<void> => {
        const roi = { x: 100, y: 100, width: 100, height: 100 };

        jest.mocked(useROI).mockReturnValueOnce({ roi, image: getMockedImage(roi) });

        const annotationToolContext = fakeAnnotationToolContext();
        const onComplete = annotationToolContext.scene.addShapes;

        await renderApp(annotationToolContext);

        const { editor } = await drawShape();

        fireEvent.pointerUp(editor, { buttons: 1, clientX: 50, clientY: 50 });

        expect(onComplete).not.toHaveBeenCalled();
    });

    it('pointerDown sets isDrawing to true and pointerUp to false', async (): Promise<void> => {
        const annotationToolContext = fakeAnnotationToolContext();
        await renderApp(annotationToolContext);

        const editor = await screen.findByRole('editor');
        fireEvent.pointerMove(editor, { clientX: 10, clientY: 10 });
        fireEvent.pointerDown(editor, { buttons: 1, clientX: 10, clientY: 10 });
        expect(annotationToolContext.scene.setIsDrawing).toHaveBeenLastCalledWith(true);

        fireEvent.pointerMove(editor, { clientX: 11, clientY: 11 });
        fireEvent.pointerUp(editor, { buttons: 1, clientX: 11, clientY: 11 });
        expect(annotationToolContext.scene.setIsDrawing).toHaveBeenLastCalledWith(false);
    });
});
