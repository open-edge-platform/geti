// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import '@wessberg/pointer-events';

import { MutableRefObject } from 'react';

import { fireEvent, screen } from '@testing-library/react';

import { Point, Polygon, Rect } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedImage } from '../../../../test-utils/utils';
import { useAddUnfinishedShape } from '../../hooks/use-add-unfinished-shape.hook';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { annotatorRender } from '../../test-utils/annotator-render';
import {
    GrabcutState,
    GrabcutStateContextProps,
    GrabcutStateProvider,
    useGrabcutState,
} from './grabcut-state-provider.component';
import { GrabcutTool } from './grabcut-tool.component';
import { GrabcutToolType } from './grabcut-tool.enums';

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        tasks: [],
        selectedTask: null,
        defaultLabel: null,
        activeDomains: [],
        isTaskChainDomainSelected: () => false,
    })),
}));

jest.mock('./grabcut-state-provider.component', () => {
    const actual = jest.requireActual('./grabcut-state-provider.component');
    return {
        ...actual,
        useGrabcutState: jest.fn(),
    };
});

jest.mock('../../hooks/use-grabcut.hook', () => ({
    useGrabcut: () => ({
        mutation: {},
        cleanModels: jest.fn(),
    }),
}));

jest.mock('../../hooks/use-add-unfinished-shape.hook', () => ({
    useAddUnfinishedShape: jest.fn(),
}));

jest.mock('./../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

const sensitivity = 10;
const strokeWidth = 10;
const mockRoi = { x: 0, y: 0, width: 100, height: 100 };
const mockRect: Rect = {
    x: mockRoi.x + 10,
    y: mockRoi.x + 10,
    width: mockRoi.width - 10,
    height: mockRoi.height - 10,
    shapeType: ShapeType.Rect,
};
const mockImage = getMockedImage(mockRoi);

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    ...jest.requireActual('../../providers/region-of-interest-provider/region-of-interest-provider.component'),
    useROI: jest.fn(() => ({
        roi: mockRoi,
        image: mockImage,
    })),
}));

const getToolSettings = jest.fn(() => ({ sensitivity }));

// @ts-expect-error We only care about mocking sensitivity
const annotationToolContext = fakeAnnotationToolContext({ getToolSettings });

jest.mocked(useAnnotationToolContext).mockReturnValue(annotationToolContext);

const renderGrabcutTool = async () => {
    const { container } = await annotatorRender(
        <GrabcutStateProvider>
            <GrabcutTool annotationToolContext={annotationToolContext} />
        </GrabcutStateProvider>
    );

    return { container };
};

const expectRunGrabcutOnce = (mockGrabcutState: GrabcutStateContextProps, inputSensitivity: number) => {
    expect(mockGrabcutState.runGrabcut).toHaveBeenNthCalledWith(1, mockImage, expect.any(Number), inputSensitivity);
};

interface GrabcutStateImplementation {
    isLoading?: boolean;
    runGrabcut?: jest.Mock;
    toolsState?: GrabcutState;
    activeTool?: GrabcutToolType;
    loadingRect?: MutableRefObject<Rect>;
    backgroundMarkers?: MutableRefObject<Point[][]>;
    foregroundMarkers?: MutableRefObject<Point[][]>;
}

const updateGrabcutStateImplementation = (data: GrabcutStateImplementation): GrabcutStateContextProps => {
    const mock: unknown = {
        strokeWidth,
        isLoading: false,
        runGrabcut: jest.fn(),
        resetConfig: jest.fn(),
        loadingRect: { current: null },
        toolsState: { polygon: null },
        foregroundMarkers: { current: [] },
        backgroundMarkers: { current: [] },
        ...data,
    };
    jest.mocked(useGrabcutState).mockReturnValueOnce(mock as GrabcutStateContextProps);
    return mock as GrabcutStateContextProps;
};

const drawRect = (editor: HTMLElement, data: { x: number; y: number; width: number; height: number }) => {
    fireEvent.pointerMove(editor, { clientX: data.x, clientY: data.y });
    fireEvent.pointerDown(editor, { buttons: 1, clientX: data.x, clientY: data.y });
    fireEvent.pointerMove(editor, { clientX: data.x + data.width, clientY: data.y + data.height });
    fireEvent.pointerUp(editor, { buttons: 1, clientX: data.x + data.width, clientY: data.y + data.height });
};

const drawMarkers = (editor: HTMLElement, markers: { x: number; y: number }[]) => {
    const [first, ...others] = markers;

    fireEvent.pointerDown(editor, { clientX: first.x, clientY: first.y, button: 0, buttons: 1 });
    others.forEach(({ x, y }) => fireEvent.pointerMove(editor, { clientX: x, clientY: y, button: 0, buttons: 1 }));

    fireEvent.pointerUp(editor);
};

describe('GrabcutTool', () => {
    it('has useAddUnfinishedShape', async () => {
        const mockGrabcutState = updateGrabcutStateImplementation({
            activeTool: GrabcutToolType.ForegroundTool,
        });
        await renderGrabcutTool();
        jest.mocked(mockGrabcutState.runGrabcut).mockReset();

        expect(useAddUnfinishedShape).toHaveBeenCalled();
    });

    describe('ForegroundTool', () => {
        it('Saves point within roi (inputRect)', async () => {
            const mockGrabcutState = updateGrabcutStateImplementation({
                toolsState: {
                    activeTool: GrabcutToolType.ForegroundTool,
                    foreground: [],
                    background: [],
                    polygon: null,
                    inputRect: mockRect,
                },
                loadingRect: { current: mockRect },
            });
            const { container } = await renderGrabcutTool();
            jest.mocked(mockGrabcutState.runGrabcut).mockReset();

            const editor = screen.getByRole('editor');
            const points = [{ x: mockRect.x + 1, y: mockRect.y + 1 }];
            drawMarkers(editor, points);

            expect(container.querySelector('polyline.inputTool')).not.toBeInTheDocument();
            expect(mockGrabcutState.foregroundMarkers).toEqual({ current: [points] });
            expectRunGrabcutOnce(mockGrabcutState, sensitivity);
        });

        it('Ignores points outside roi (inputRect)', async () => {
            const mockGrabcutState = updateGrabcutStateImplementation({
                toolsState: {
                    activeTool: GrabcutToolType.ForegroundTool,
                    foreground: [],
                    background: [],
                    polygon: null,
                    inputRect: mockRect,
                },
                loadingRect: { current: mockRect },
            });
            const { container } = await renderGrabcutTool();
            jest.mocked(mockGrabcutState.runGrabcut).mockReset();

            const editor = screen.getByRole('editor');
            const invalidPoints = [{ x: mockRect.x - 1, y: mockRect.y }];
            const points = [{ x: mockRect.x + 1, y: mockRect.y + 1 }];
            drawMarkers(editor, [...points, ...invalidPoints]);

            expect(container.querySelector('polyline.inputTool')).not.toBeInTheDocument();
            expect(mockGrabcutState.foregroundMarkers).toEqual({ current: [points] });
            expectRunGrabcutOnce(mockGrabcutState, sensitivity);
        });
    });

    it('Multiple points, save the points and call runGrabcut', async () => {
        const mockGrabcutState = updateGrabcutStateImplementation({
            toolsState: {
                activeTool: GrabcutToolType.BackgroundTool,
                foreground: [],
                background: [],
                polygon: null,
                inputRect: mockRect,
            },
            loadingRect: { current: mockRect },
        });
        const { container } = await renderGrabcutTool();
        jest.mocked(mockGrabcutState.runGrabcut).mockReset();

        const editor = screen.getByRole('editor');

        const [pointsOne, pointsTwo] = [
            [{ x: mockRect.x + 1, y: mockRect.y + 1 }],
            [{ x: mockRect.x + 2, y: mockRect.y + 2 }],
        ];
        drawMarkers(editor, pointsOne);
        drawMarkers(editor, pointsTwo);

        expect(container.querySelector('polyline.inputTool')).not.toBeInTheDocument();
        expect(mockGrabcutState.backgroundMarkers).toEqual({ current: [pointsOne, pointsTwo] });
        expectRunGrabcutOnce(mockGrabcutState, sensitivity);
    });

    it('render PolygonDraw with ".inputTool" when loading is true', async () => {
        updateGrabcutStateImplementation({
            isLoading: true,
            toolsState: {
                activeTool: GrabcutToolType.InputTool,
                inputRect: mockRect,
                background: [],
                foreground: [],
                polygon: {
                    shapeType: ShapeType.Polygon,
                    points: [
                        { x: 4, y: 42 },
                        { x: 5, y: 43 },
                    ],
                },
            },
        });
        const { container } = await renderGrabcutTool();
        const loadingPolyline = container.querySelector('polyline.inputTool') as SVGAElement;

        expect(loadingPolyline).toBeInTheDocument();
    });

    describe('InputTool', () => {
        it('call resetConfig and run runGrabcut after drawing an inputRect', async () => {
            const mockGrabcutState = updateGrabcutStateImplementation({
                toolsState: {
                    activeTool: GrabcutToolType.InputTool,
                    foreground: [],
                    background: [],
                    polygon: null,
                    inputRect: mockRect,
                },
            });
            await renderGrabcutTool();
            jest.mocked(mockGrabcutState.runGrabcut).mockReset();

            const editor = await screen.findByRole('editor');
            const rectValues = { x: 10, y: 10, width: 50, height: 50 };
            drawRect(editor, rectValues);

            expect(mockGrabcutState.loadingRect.current).toEqual({ ...rectValues, shapeType: ShapeType.Rect });
            expect(mockGrabcutState.resetConfig).toHaveBeenCalled();
            expectRunGrabcutOnce(mockGrabcutState, sensitivity);
            expect(annotationToolContext.scene.addShapes).not.toHaveBeenCalled();
        });

        it('accept the previous annotation (call addShapes) with annotation selected false', async () => {
            const polygon: Polygon = { shapeType: ShapeType.Polygon, points: [{ x: 10, y: 10 }] };
            const mockGrabcutState = updateGrabcutStateImplementation({
                toolsState: {
                    polygon,
                    background: [],
                    foreground: [],
                    inputRect: mockRect,
                    activeTool: GrabcutToolType.InputTool,
                },
            });

            await renderGrabcutTool();
            jest.mocked(mockGrabcutState.runGrabcut).mockReset();

            const editor = await screen.findByRole('editor');
            const rectValues = { x: 10, y: 10, width: 50, height: 50 };
            drawRect(editor, rectValues);

            expect(mockGrabcutState.resetConfig).toHaveBeenCalled();
            expectRunGrabcutOnce(mockGrabcutState, sensitivity);
            expect(annotationToolContext.scene.addShapes).toHaveBeenCalledWith([polygon], undefined, false);
            expect(mockGrabcutState.loadingRect.current).toEqual({ ...rectValues, shapeType: ShapeType.Rect });
        });

        it('render a loadingRect when loading is true', async () => {
            const rect: Rect = {
                x: 10,
                y: 10,
                width: 100,
                height: 100,
                shapeType: ShapeType.Rect,
            };
            const mockGrabcutState = updateGrabcutStateImplementation({
                isLoading: true,
                loadingRect: {
                    current: rect,
                },
                toolsState: {
                    activeTool: GrabcutToolType.InputTool,
                    foreground: [],
                    background: [],
                    polygon: null,
                    inputRect: mockRect,
                },
            });

            const { container } = await renderGrabcutTool();
            jest.mocked(mockGrabcutState.runGrabcut).mockReset();

            const loadingRect = container.querySelector('rect.inputTool') as SVGAElement;

            expect(loadingRect.getAttribute('x')).toBe(`${rect.x}`);
            expect(loadingRect.getAttribute('y')).toBe(`${rect.y}`);
            expect(loadingRect.getAttribute('width')).toBe(`${rect.width}`);
            expect(loadingRect.getAttribute('height')).toBe(`${rect.height}`);
        });
    });
});
