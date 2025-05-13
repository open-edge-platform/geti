// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent } from 'react';

import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { act, renderHook } from '@testing-library/react';

import { Point } from '../../../core/annotations/shapes.interface';
import { AlgorithmType } from '../../../hooks/use-load-ai-webworker/algorithm.interface';
import { getMockedImage } from '../../../test-utils/utils';
import { BUTTON_LEFT, BUTTON_RIGHT } from '../../buttons-utils';
import { PolygonStateContextProps, usePolygonState } from '../tools/polygon-tool/polygon-state-provider.component';
import { PolygonMode } from '../tools/polygon-tool/polygon-tool.enum';
import { IntelligentScissorsWorker } from '../tools/polygon-tool/polygon-tool.interface';
import { PointerType } from '../tools/tools.interface';
import { IntelligentScissorsProps, useIntelligentScissors } from './use-intelligent-scissors.hook';

jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useMutation: jest.fn(),
}));

jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({
        addNotification: jest.fn(),
    }),
}));

jest.mock('../tools/polygon-tool/polygon-state-provider.component', () => ({
    ...jest.requireActual('../tools/polygon-tool/polygon-state-provider.component'),
    usePolygonState: jest.fn(),
}));

const intelligentScissorMock: IntelligentScissorsWorker = {
    waitForOpenCV: jest.fn(),
    IntelligentScissors: jest.fn(() => ({
        applyImage: jest.fn(),
        hasInitialPoint: false,
        loadTool: jest.fn(),
        cleanImg: jest.fn(),
        cleanPoints: jest.fn(),
        buildMap: jest.fn(),
        calcPoints: jest.fn(),
    })),
    optimizeSegments: jest.fn(),
    terminate: jest.fn(),
    optimizePolygon: jest.fn(),
    type: AlgorithmType.INTELLIGENT_SCISSORS,
};

const mockProps = ({ canPathBeClosed = false }: { canPathBeClosed?: boolean }): IntelligentScissorsProps => ({
    zoom: 1,
    polygon: null,
    lassoSegment: [],
    image: getMockedImage(),
    complete: jest.fn(),
    setPointerLine: jest.fn(() => []),
    setLassoSegment: jest.fn(() => []),
    canPathBeClosed: () => canPathBeClosed,
    setPointFromEvent: jest.fn(
        (callback: (point: Point) => void) => (event: PointerEvent<SVGElement>) =>
            callback({ x: event.clientX, y: event.clientY })
    ),
    // @ts-expect-error expect issue with comlink's Remote
    worker: intelligentScissorMock,
    handleIsStartingPointHovered: jest.fn(),
});

interface iMockEvent {
    button?: number;
    buttons?: number;
    pointerType?: PointerType;
}

const mockEvent = ({
    button = BUTTON_LEFT.button,
    buttons = BUTTON_LEFT.buttons,
    pointerType = PointerType.Mouse,
}: iMockEvent): unknown => ({
    preventDefault: jest.fn(),
    pointerType,
    button,
    buttons,
    clientX: 10,
    clientY: 20,
});

const updateUseMutation = () => {
    const mocks: unknown = {
        mutate: jest.fn(),
    };

    jest.mocked(useMutation).mockImplementationOnce(() => mocks as UseMutationResult);

    return mocks as UseMutationResult;
};

const updateUsePolygonState = ({ segments = [] }: { segments?: Point[] }) => {
    const mocks: unknown = {
        segments,
        mode: PolygonMode.MagneticLasso,
        setMode: jest.fn(),
        setSegments: jest.fn(),
        undoRedoActions: jest.fn(),
        isIntelligentScissorsLoaded: false,
        setIsIntelligentScissorsLoaded: jest.fn(),
    };

    jest.mocked(usePolygonState).mockImplementationOnce(() => mocks as PolygonStateContextProps);

    return mocks as PolygonStateContextProps;
};

describe('useIntelligentScissors', () => {
    afterAll(() => {
        jest.resetAllMocks();
    });

    describe('onPointerDown', () => {
        it('call preventDefault when pointerType is "Touch"', () => {
            const hookProps = mockProps({});
            const polygonState = updateUsePolygonState({});
            const { result } = renderHook(() => useIntelligentScissors(hookProps));
            const event = mockEvent({ ...BUTTON_RIGHT, pointerType: PointerType.Touch }) as PointerEvent<SVGSVGElement>;

            act(() => {
                result.current.onPointerDown(event);
            });

            expect(event.preventDefault).toBeCalled();
            expect(polygonState.setMode).not.toHaveBeenCalled();
            expect(hookProps.setLassoSegment).not.toHaveBeenCalled();
            expect(polygonState.setSegments).not.toHaveBeenCalled();
        });

        it('call setMode Eraser when is right click', () => {
            const hookProps = mockProps({});
            const polygonState = updateUsePolygonState({});
            const { result } = renderHook(() => useIntelligentScissors(hookProps));
            const event = mockEvent({ ...BUTTON_RIGHT }) as PointerEvent<SVGSVGElement>;

            act(() => {
                result.current.onPointerDown(event);
            });

            expect(event.preventDefault).toBeCalled();
            expect(hookProps.setLassoSegment).not.toHaveBeenCalled();
            expect(polygonState.setSegments).not.toHaveBeenCalled();
            expect(polygonState.setMode).toHaveBeenCalledWith(PolygonMode.Eraser);
        });

        it('call setLassoSegment and setSegments when buildMapPoint is empty', () => {
            const hookProps = mockProps({});
            const polygonState = updateUsePolygonState({});
            const { result } = renderHook(() => useIntelligentScissors(hookProps));
            const event = mockEvent({}) as PointerEvent<SVGSVGElement>;

            act(() => {
                result.current.onPointerDown(event);
            });

            expect(hookProps.complete).not.toHaveBeenCalledWith(PolygonMode.MagneticLasso);
            expect(hookProps.setLassoSegment).toHaveBeenCalledWith([]);
            expect(polygonState.setSegments).toHaveBeenCalledWith([[{ x: event.clientX, y: event.clientY }]]);
        });
    });

    describe('onPointerMove', () => {
        it('unless segments have info do nothing', () => {
            const hookProps = mockProps({});

            updateUsePolygonState({});

            const mutationData = updateUseMutation();
            const { result } = renderHook(() => useIntelligentScissors(hookProps));

            act(() => {
                result.current.onPointerMove(mockEvent({}) as PointerEvent<SVGSVGElement>);
            });

            expect(hookProps.complete).not.toHaveBeenCalled();
            expect(hookProps.setPointerLine).not.toHaveBeenCalled();
            expect(hookProps.setLassoSegment).not.toHaveBeenCalled();
            expect(mutationData.mutate).not.toHaveBeenCalled();
        });

        it('call mutation handler when sections are not empty', () => {
            const hookProps = mockProps({});
            const mutationData = updateUseMutation();
            const point = { x: 10, y: 20 };

            updateUsePolygonState({ segments: [point] });

            const { result } = renderHook(() => useIntelligentScissors(hookProps));

            act(() => {
                result.current.onPointerMove(mockEvent({}) as PointerEvent<SVGSVGElement>);
            });

            expect(mutationData.mutate).toHaveBeenCalledWith(point);
            expect(hookProps.complete).not.toHaveBeenCalled();
            expect(hookProps.setPointerLine).not.toHaveBeenCalled();
            expect(hookProps.setLassoSegment).not.toHaveBeenCalled();
        });

        it('call setLassoSegment and setSegments when isFreeDrawing is true', () => {
            const hookProps = mockProps({});
            const point = { x: 10, y: 20 };

            updateUsePolygonState({ segments: [point] });

            const mutationData = updateUseMutation();
            const { result } = renderHook(() => useIntelligentScissors(hookProps));
            const event = mockEvent({}) as PointerEvent<SVGSVGElement>;

            act(() => {
                result.current.onPointerDown(event);
                jest.mocked(hookProps.setLassoSegment).mockReset();
                result.current.onPointerMove(event);
            });

            expect(hookProps.complete).not.toHaveBeenCalled();
            expect(mutationData.mutate).not.toHaveBeenCalled();
            expect(hookProps.setPointerLine).toHaveBeenCalledTimes(1);
            expect(hookProps.setLassoSegment).toHaveBeenCalledTimes(1);
        });

        it('call handleIsStartingPointHovered when moving', () => {
            const hookProps = mockProps({});
            const point = { x: 10, y: 20 };

            updateUsePolygonState({ segments: [point] });

            const { result } = renderHook(() => useIntelligentScissors(hookProps));
            const event = mockEvent({}) as PointerEvent<SVGSVGElement>;

            act(() => {
                result.current.onPointerDown(event);
                result.current.onPointerMove(event);
            });

            expect(hookProps.handleIsStartingPointHovered).toHaveBeenCalledWith(point);
        });
    });

    describe('onPointerUp', () => {
        it('call setLassoSegment and setSegments when isFreeDrawing and canPathBeClosed is false', () => {
            const hookProps = mockProps({});
            const polygonState = updateUsePolygonState({ segments: [{ x: 10, y: 20 }] });
            const { result } = renderHook(() => useIntelligentScissors(hookProps));
            const event = mockEvent({}) as PointerEvent<SVGSVGElement>;

            act(() => {
                result.current.onPointerDown(event);
                result.current.onPointerMove(event);

                jest.mocked(hookProps.setLassoSegment).mockReset();
                jest.mocked(polygonState.setSegments).mockReset();

                result.current.onPointerUp(event);
            });

            expect(hookProps.complete).not.toBeCalled();
            expect(hookProps.setLassoSegment).toHaveBeenCalledWith([]);
            expect(polygonState.setSegments).toHaveBeenCalledTimes(1);
        });

        it('call complete when canPathBeClosed', () => {
            updateUseMutation();

            const hookProps = mockProps({ canPathBeClosed: true });
            const polygonState = updateUsePolygonState({ segments: [{ x: 10, y: 20 }] });
            const { result } = renderHook(() => useIntelligentScissors(hookProps));
            const event = mockEvent({}) as PointerEvent<SVGSVGElement>;

            act(() => {
                result.current.onPointerDown(event);
                result.current.onPointerMove(event);

                jest.mocked(hookProps.setLassoSegment).mockReset();
                jest.mocked(polygonState.setSegments).mockReset();

                result.current.onPointerUp(event);
            });

            expect(polygonState.setSegments).not.toHaveBeenCalled();
            expect(hookProps.setLassoSegment).not.toHaveBeenCalled();
            expect(hookProps.complete).toHaveBeenCalledWith(PolygonMode.MagneticLasso);
        });
    });
});
