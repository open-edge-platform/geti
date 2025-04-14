// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { Rect } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getById } from '../../../../test-utils/utils';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { annotatorRender } from '../../test-utils/annotator-render';
import {
    GrabcutState,
    GrabcutStateContextProps,
    GrabcutStateProvider,
    useGrabcutState,
} from './grabcut-state-provider.component';
import { GrabcutToolType } from './grabcut-tool.enums';
import { SecondaryToolbar } from './secondary-toolbar.component';

jest.mock('../../providers/annotator-provider/annotator-provider.component', () => ({
    ...jest.requireActual('../../providers/annotator-provider/annotator-provider.component'),
    useAnnotator: jest.fn(() => ({
        hotKeys: {
            close: 'escape',
            accept: 'enter',
        },
    })),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('./grabcut-state-provider.component', () => {
    const actual = jest.requireActual('./grabcut-state-provider.component');
    return {
        ...actual,
        useGrabcutState: jest.fn(() => ({
            ...actual.useGrabcutState(),
        })),
    };
});

jest.mock('../../hooks/use-grabcut.hook', () => ({
    useGrabcut: () => ({
        mutation: {},
        cleanModels: jest.fn(),
    }),
}));

const getToolSettings = jest.fn(() => ({ sensitivity: 20 }));

// @ts-expect-error We only care about mocking sensitivity
const annotationToolContext = fakeAnnotationToolContext({ getToolSettings });
const mockRect: Rect = { x: 10, y: 10, width: 100, height: 100, shapeType: ShapeType.Rect };

jest.mocked(useAnnotationToolContext).mockReturnValue(annotationToolContext);

const renderToolbar = async () => {
    const { container } = await annotatorRender(
        <GrabcutStateProvider>
            <SecondaryToolbar annotationToolContext={annotationToolContext} />
        </GrabcutStateProvider>
    );

    return container;
};

const updateGrabcutStateImplementation = (data: Partial<GrabcutStateContextProps>) => {
    jest.mocked(useGrabcutState).mockImplementationOnce(() => {
        const actual = jest.requireActual('./grabcut-state-provider.component');
        const defaultOptions = {
            toolsState: { polygon: {}, sensitivity: 20, activeTool: GrabcutToolType.InputTool },
            setSensitivity: jest.fn(),
        };

        return {
            ...actual,
            ...defaultOptions,
            ...data,
        };
    });
};

const expectDisableTool = (container: HTMLElement, label: string) => {
    const tool = getById(container, label);

    expect(tool).toBeInTheDocument();
    expect(tool).toHaveAttribute('disabled');
};

const toolsState: GrabcutState = {
    polygon: {
        shapeType: ShapeType.Polygon,
        points: [
            { x: 1, y: 1 },
            { x: 2, y: 2 },
            { x: 3, y: 3 },
        ],
    },
    inputRect: null,
    background: [],
    foreground: [],
    activeTool: GrabcutToolType.InputTool,
};

describe('Grabcut Secondary Toolbar', () => {
    it('has title "Quick selection"', async () => {
        await renderToolbar();

        expect(screen.getByText('Quick selection')).toBeInTheDocument();
    });

    it('has InputTool selected by default', async () => {
        const container = await renderToolbar();

        const grabcutInputTool = getById(container, GrabcutToolType.InputTool);

        expect(grabcutInputTool).toBeInTheDocument();
        expect(grabcutInputTool).toHaveAttribute('aria-pressed', 'true');
    });

    it('InputTool is disabled when runGrabcut is loading', async () => {
        updateGrabcutStateImplementation({
            loadingRect: { current: mockRect },
            isLoading: true,
        });

        const container = await renderToolbar();

        expectDisableTool(container, GrabcutToolType.InputTool);
    });

    it('has ForegroundTool disabled', async () => {
        const container = await renderToolbar();

        expectDisableTool(container, GrabcutToolType.ForegroundTool);
    });

    it('ForegroundTool is disabled when runGrabcut is loading', async () => {
        updateGrabcutStateImplementation({
            loadingRect: { current: mockRect },
            isLoading: true,
        });

        const container = await renderToolbar();

        expectDisableTool(container, GrabcutToolType.ForegroundTool);
    });

    it('has BackgroundTool disabled', async () => {
        const container = await renderToolbar();
        expectDisableTool(container, GrabcutToolType.BackgroundTool);
    });

    it('BackgroundTool is disabled when runGrabcut is loading', async () => {
        updateGrabcutStateImplementation({
            loadingRect: { current: mockRect },
            isLoading: true,
        });

        const container = await renderToolbar();

        expectDisableTool(container, GrabcutToolType.BackgroundTool);
    });

    it('has sensitivity slider', async () => {
        await renderToolbar();

        expect(screen.getByText('Sensitivity:')).toBeInTheDocument();
    });

    it('Sensitivity slider is disabled when runGrabcut is loading', async () => {
        updateGrabcutStateImplementation({
            loadingRect: { current: mockRect },
            isLoading: true,
        });

        await renderToolbar();

        expect(screen.getByLabelText('Sensitivity button')).toBeDisabled();
    });

    describe('has acceptance tools and polygon', () => {
        const resetConfig = jest.fn();
        const rejectAnnotation = jest.fn();

        const getRejectButton = () => screen.getByLabelText('reject grabcut annotation');
        const getAcceptButton = () => screen.getByLabelText('accept grabcut annotation');

        beforeEach(() => {
            updateGrabcutStateImplementation({
                toolsState: {
                    activeTool: GrabcutToolType.InputTool,
                    inputRect: { shapeType: ShapeType.Rect, x: 0, y: 10, width: 100, height: 110 },
                    polygon: {
                        shapeType: ShapeType.Polygon,
                        points: [
                            { x: 1, y: 1 },
                            { x: 2, y: 2 },
                            { x: 3, y: 3 },
                        ],
                    },
                    background: [],
                    foreground: [],
                },
                resetConfig,
                rejectAnnotation,
                isLoading: true,
            });
        });

        it('has reject annotation option', async () => {
            await renderToolbar();

            expect(getRejectButton()).toBeInTheDocument();
        });

        it('has accept annotation option', async () => {
            await renderToolbar();

            expect(getAcceptButton()).toBeInTheDocument();
        });

        it('should add the shape and reset the tools config', async () => {
            await renderToolbar();

            fireEvent.click(getAcceptButton());

            expect(annotationToolContext.scene.addShapes).toHaveBeenCalledWith([toolsState.polygon], undefined);
            expect(resetConfig).toHaveBeenCalled();
        });

        it('should reset the tools config', async () => {
            await renderToolbar();

            fireEvent.click(getRejectButton());

            expect(rejectAnnotation).toHaveBeenCalled();
        });
    });

    describe('hotkeys', () => {
        const setToolsState = jest.fn((...args) => {
            const [fun] = args;

            return fun({});
        });

        beforeEach(() => {
            setToolsState.mockClear();
        });

        it('ForegroundTool, should call setActiveTool', async () => {
            updateGrabcutStateImplementation({ setToolsState, isLoading: false });
            const container = await renderToolbar();

            fireEvent.keyDown(container, {
                key: 'Shift',
                code: 'ShiftLeft',
                keyCode: 16,
                charCode: 0,
            });

            expect(setToolsState).toHaveReturnedWith({ activeTool: GrabcutToolType.ForegroundTool });
        });

        it('BackgroundTool, should call setActiveTool', async () => {
            updateGrabcutStateImplementation({ setToolsState, isLoading: false });
            const container = await renderToolbar();

            fireEvent.keyDown(container, {
                key: 'Alt',
                code: 'AltLeft',
                keyCode: 18,
            });

            expect(setToolsState).toHaveReturnedWith({ activeTool: GrabcutToolType.BackgroundTool });
        });

        it('should not call setActiveTool when toolsState is null', async () => {
            updateGrabcutStateImplementation({
                setToolsState,
                // @ts-expect-error We care about mocking polygon
                toolsState: {
                    polygon: null,
                },
                isLoading: false,
            });
            const container = await renderToolbar();

            fireEvent.keyDown(container, {
                key: 'Shift',
                code: 'ShiftLeft',
                keyCode: 16,
            });

            expect(setToolsState).not.toHaveBeenCalled();

            fireEvent.keyDown(container, {
                key: 'Alt',
                code: 'AltLeft',
                keyCode: 18,
                charCode: 0,
            });

            expect(setToolsState).not.toHaveBeenCalled();
        });

        it('updates active tool to "inputTool"', async () => {
            updateGrabcutStateImplementation({ setToolsState, isLoading: false });
            await renderToolbar();

            fireEvent.click(screen.getByLabelText('New selection'));
            expect(setToolsState).toHaveReturnedWith({ activeTool: GrabcutToolType.InputTool });
        });

        it('updates active tool to "ForegroundTool"', async () => {
            updateGrabcutStateImplementation({ setToolsState, isLoading: false, toolsState });
            await renderToolbar();

            fireEvent.click(screen.getByLabelText('Add to selection'));
            expect(setToolsState).toHaveReturnedWith({ activeTool: GrabcutToolType.ForegroundTool });
        });

        it('updates active tool to "BackgroundTool"', async () => {
            updateGrabcutStateImplementation({ setToolsState, isLoading: false, toolsState });
            await renderToolbar();

            fireEvent.click(screen.getByLabelText('Subtract from selection'));
            expect(setToolsState).toHaveReturnedWith({ activeTool: GrabcutToolType.BackgroundTool });
        });
    });
});
