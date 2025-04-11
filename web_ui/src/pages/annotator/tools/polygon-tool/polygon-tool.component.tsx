// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { PointerEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';

import differenceWith from 'lodash/differenceWith';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';

import { clampPointBetweenImage, isPointOverPoint } from '../../../../core/annotations/math';
import { Point, Polygon } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { useLoadAIWebworker } from '../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { KeyboardEvents } from '../../../../shared/keyboard-events/keyboard.interface';
import { onEscape } from '../../../../shared/utils';
import { getRelativePoint } from '../../../utils';
import { useIntelligentScissors } from '../../hooks/use-intelligent-scissors.hook';
import { usePolygon } from '../../hooks/use-polygon.hook';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { PolygonDraw } from '../polygon-draw.component';
import { SvgToolCanvas } from '../svg-tool-canvas.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles, isPolygonValid, removeOffLimitPointsPolygon } from '../utils';
import { usePolygonState } from './polygon-state-provider.component';
import { PointerIcons, PointerIconsOffset, PolygonMode } from './polygon-tool.enum';
import { isCloseMode, START_POINT_FIELD_DEFAULT_RADIUS, START_POINT_FIELD_FOCUS_RADIUS } from './utils';

import classes from './polygon-tool.module.scss';

const getCloseMode = (mode: PolygonMode | null) => {
    if (mode === PolygonMode.MagneticLasso) {
        return PolygonMode.MagneticLassoClose;
    }

    if (mode === PolygonMode.Lasso) {
        return PolygonMode.LassoClose;
    }

    return PolygonMode.PolygonClose;
};

const TOOL_ICON: Record<PolygonMode, { icon: PointerIcons; offset: PointerIconsOffset }> = {
    [PolygonMode.Polygon]: { icon: PointerIcons.Polygon, offset: PointerIconsOffset.Polygon },
    [PolygonMode.Eraser]: { icon: PointerIcons.Eraser, offset: PointerIconsOffset.Eraser },
    [PolygonMode.Lasso]: { icon: PointerIcons.Lasso, offset: PointerIconsOffset.Lasso },
    [PolygonMode.LassoClose]: { icon: PointerIcons.LassoClose, offset: PointerIconsOffset.LassoClose },
    [PolygonMode.MagneticLasso]: { icon: PointerIcons.MagneticLasso, offset: PointerIconsOffset.MagneticLasso },
    [PolygonMode.MagneticLassoClose]: {
        icon: PointerIcons.MagneticLassoClose,
        offset: PointerIconsOffset.MagneticLassoClose,
    },
    [PolygonMode.PolygonClose]: { icon: PointerIcons.PolygonClose, offset: PointerIconsOffset.PolygonClose },
};

const getToolIcon = (polygonMode: PolygonMode | null) => {
    if (polygonMode === null) {
        return TOOL_ICON[PolygonMode.Polygon];
    }

    return TOOL_ICON[polygonMode];
};

export const PolygonTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { scene } = annotationToolContext;

    const { defaultLabel } = useTask();
    const { setIsDrawing } = useAnnotationScene();
    const ref = useRef<SVGRectElement>({} as SVGRectElement);
    const isClosing = useRef(false);
    const {
        zoomState: { zoom },
    } = useZoom();

    const { roi, image } = useROI();

    const [isOptimizingPolygons, setIsOptimizingPolygons] = useState(false);
    const [polygon, setPolygon] = useState<Polygon | null>(null);
    const [pointerLine, setPointerLine] = useState<Point[]>([]);
    const [lassoSegment, setLassoSegment] = useState<Point[]>([]);

    const { segments, undoRedoActions, mode, setMode } = usePolygonState();

    const { worker } = useLoadAIWebworker(AlgorithmType.INTELLIGENT_SCISSORS);

    const previousPolygonMode = useRef<PolygonMode | null>(null);

    // START_POINT_FIELD_FOCUS_RADIUS / zoom ~ 16 px
    // START_POINT_FIELD_DEFAULT_RADIUS / zoom ~ 12 px
    const STARTING_POINT_RADIUS = useMemo(
        () => Math.ceil((isCloseMode(mode) ? START_POINT_FIELD_FOCUS_RADIUS : START_POINT_FIELD_DEFAULT_RADIUS) / zoom),
        [mode, zoom]
    );

    const toolIcon = getToolIcon(mode);

    const resetMode = (inputMode: PolygonMode | null = null) => {
        setMode(inputMode);
    };

    const reset = useCallback(
        (): void => {
            undoRedoActions.reset();

            setPointerLine([]);
            setLassoSegment([]);
            setPolygon(null);
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [undoRedoActions.reset]
    );

    useEffect(() => {
        if (mode) {
            // NOTE: We don't want to reset the mode. Imagine case when user used snapping mode, changed tool to circle
            // and then decided to use polygon again. We want to allow user to use previous polygon configuration.
            reset();
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [image, reset]);

    const onComplete = (optimizedPolygon: Polygon) => {
        !isEmpty(optimizedPolygon.points) && scene.addShapes([optimizedPolygon]);
    };

    useEventListener(
        KeyboardEvents.KeyDown,
        onEscape(() => {
            setMode(null);
            reset();
        })
    );

    const getPointerRelativePosition = useCallback(
        (event: PointerEvent<SVGElement>): Point => {
            const clampPoint = clampPointBetweenImage(image);

            return clampPoint(getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom));
        },
        [image, zoom]
    );

    const optimizePolygonOrSegments = (iPolygon: Polygon): Promise<Polygon> => {
        if (worker) {
            if (mode === PolygonMode.MagneticLasso) {
                return worker.optimizePolygon(iPolygon);
            }

            const lastSegment = differenceWith(iPolygon.points, segments.flat(), isEqual);
            const newSegments = isEmpty(lastSegment) ? [...segments] : [...segments, lastSegment];

            return worker.optimizeSegments(newSegments);
        } else {
            return Promise.reject();
        }
    };

    const complete = useCallback(
        async (inputMode: PolygonMode | null) => {
            if (!polygon || isClosing.current) return;

            isClosing.current = true;
            polygon.points.pop();

            if (isPolygonValid(polygon)) {
                setIsOptimizingPolygons(true);

                const optimizedPolygon = await optimizePolygonOrSegments(polygon);

                onComplete(removeOffLimitPointsPolygon(optimizedPolygon, roi));
                setIsOptimizingPolygons(false);
            }

            reset();
            resetMode(inputMode);
            isClosing.current = false;
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [roi, onComplete, polygon, reset, mode]
    );

    useEffect((): void => setPolygon({ shapeType: ShapeType.Polygon, points: segments?.flat() }), [segments]);

    useEffect((): void => setPolygon({ shapeType: ShapeType.Polygon, points: pointerLine }), [pointerLine]);

    const setPointFromEvent = (callback: (point: Point) => void) => (event: PointerEvent<SVGElement>) =>
        callback(getPointerRelativePosition(event));

    const canPathBeClosed = useCallback(
        (point: Point): boolean => {
            const flatSegments = segments.flat();

            if (isEmpty(flatSegments)) return false;

            return (
                Boolean(polygon) &&
                isPolygonValid(polygon) &&
                isPointOverPoint(flatSegments[0], point, STARTING_POINT_RADIUS)
            );
        },
        [polygon, segments, STARTING_POINT_RADIUS]
    );

    const handleIsStartingPointHovered = useCallback(
        (point: Point): void => {
            if (!isCloseMode(mode) && canPathBeClosed(point)) {
                // store the previously used polygon mode
                previousPolygonMode.current = mode;

                setMode(getCloseMode(mode));
            }

            if (isCloseMode(mode) && !canPathBeClosed(point)) {
                setMode(previousPolygonMode.current);
            }
        },
        [mode, canPathBeClosed, previousPolygonMode, setMode]
    );

    const magneticLassoHandlers = useIntelligentScissors({
        zoom,
        image,
        worker,
        polygon,
        complete,
        lassoSegment,
        setPointerLine,
        setLassoSegment,
        canPathBeClosed,
        setPointFromEvent,
        handleIsStartingPointHovered,
    });

    const polygonHandlers = usePolygon({
        zoom,
        polygon,
        complete,
        lassoSegment,
        setPointerLine,
        setLassoSegment,
        canPathBeClosed,
        setPointFromEvent,
        handleIsStartingPointHovered,
    });

    const eventHandlers = mode === PolygonMode.MagneticLasso ? magneticLassoHandlers : polygonHandlers;

    return (
        <SvgToolCanvas
            image={image}
            canvasRef={ref}
            onPointerUp={(event) => {
                setIsDrawing(false);
                eventHandlers.onPointerUp(event);
            }}
            onPointerDown={(event) => {
                setIsDrawing(true);
                eventHandlers.onPointerDown(event);
            }}
            onPointerMove={eventHandlers.onPointerMove}
            onPointerLeave={eventHandlers.onPointerMove}
            style={{ cursor: `url(/icons/cursor/${toolIcon.icon}.png) ${toolIcon.offset}, auto` }}
        >
            {polygon !== null && !isEmpty(polygon.points) && (
                <PolygonDraw
                    shape={polygon}
                    ariaLabel='new polygon'
                    styles={drawingStyles(defaultLabel)}
                    className={isOptimizingPolygons ? classes.inputTool : ''}
                    indicatorRadius={STARTING_POINT_RADIUS}
                />
            )}
        </SvgToolCanvas>
    );
};
