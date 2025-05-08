// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, useCallback, useEffect, useRef } from 'react';

import { isEmpty } from 'lodash-es';

import { getIntersectionPoint } from '../../../core/annotations/math';
import { Point, Polygon } from '../../../core/annotations/shapes.interface';
import { leftRightMouseButtonHandler } from '../../utils';
import { usePolygonState } from '../tools/polygon-tool/polygon-state-provider.component';
import { PolygonMode } from '../tools/polygon-tool/polygon-tool.enum';
import { MouseEventHandlers } from '../tools/polygon-tool/polygon-tool.interface';
import {
    deleteSegments,
    ERASER_FIELD_DEFAULT_RADIUS,
    isCloseMode,
    removeEmptySegments,
} from '../tools/polygon-tool/utils';
import { SetStateWrapper } from '../tools/undo-redo/use-undo-redo-state';

interface UsePolygonProps {
    zoom: number;
    polygon: Polygon | null;
    lassoSegment: Point[];
    canPathBeClosed: (point: Point) => boolean;
    setPointerLine: SetStateWrapper<Point[]>;
    setLassoSegment: SetStateWrapper<Point[]>;
    complete: (resetMode: PolygonMode | null) => void;
    setPointFromEvent: (callback: (point: Point) => void) => (event: PointerEvent<SVGElement>) => void;
    handleIsStartingPointHovered: (point: Point) => void;
}

export const usePolygon = ({
    zoom,
    polygon,
    complete,
    lassoSegment,
    setPointerLine,
    canPathBeClosed,
    setLassoSegment,
    setPointFromEvent,
    handleIsStartingPointHovered,
}: UsePolygonProps): MouseEventHandlers => {
    const { segments, setSegments, mode, setMode } = usePolygonState();
    const prevMainMode = useRef<PolygonMode | null>(null);
    const isPointerDown = useRef<boolean>(false);

    useEffect(() => {
        if (!isCloseMode(mode) && prevMainMode.current === PolygonMode.MagneticLasso) {
            setLassoSegment([]);
        }

        if (mode !== PolygonMode.Eraser && mode !== PolygonMode.Lasso) {
            prevMainMode.current = mode;
        }
    }, [mode, setLassoSegment]);

    // eslint-disable-next-line react-hooks/exhaustive-deps
    const onPointerDown = useCallback(
        leftRightMouseButtonHandler(
            (event) => {
                event.currentTarget.setPointerCapture(event.pointerId);

                setPointFromEvent((point: Point) => {
                    setMode(PolygonMode.Polygon);

                    isPointerDown.current = true;

                    if (canPathBeClosed(point)) {
                        isPointerDown.current = false;

                        return;
                    }

                    setSegments(removeEmptySegments(lassoSegment, [point]));
                    setLassoSegment([]);
                })(event);
            },
            (event) => {
                if (isEmpty(segments)) return;

                event.currentTarget.setPointerCapture(event.pointerId);

                setMode(PolygonMode.Eraser);
            }
        ),
        [complete, setSegments, setMode, setLassoSegment]
    );

    const onPointerUp = useCallback(
        (event: PointerEvent<SVGSVGElement>) => {
            event.currentTarget.releasePointerCapture(event.pointerId);

            setPointFromEvent((point: Point): void => {
                // finish the drawing while releasing the button inside the area of starting point
                if ((mode === PolygonMode.Lasso || isCloseMode(mode)) && polygon) {
                    setSegments(removeEmptySegments(lassoSegment));
                    setLassoSegment([]);
                }

                if (canPathBeClosed(point)) {
                    //Note: to not clear snapping mode state
                    const expectedMode = mode === PolygonMode.MagneticLassoClose ? mode : null;
                    complete(expectedMode);
                }

                setMode(prevMainMode.current);
                isPointerDown.current = false;
            })(event);
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [lassoSegment, mode, polygon]
    );

    // eslint-disable-next-line react-hooks/exhaustive-deps
    const onPointerMove = useCallback(
        setPointFromEvent((newPoint: Point) => {
            if (isEmpty(segments)) return;

            if (mode === PolygonMode.Polygon && isPointerDown.current) setMode(PolygonMode.Lasso);

            if (mode === PolygonMode.Lasso) {
                setLassoSegment((newLassoSegment: Point[]) => [...newLassoSegment, newPoint]);
            }

            if (mode === PolygonMode.Eraser) {
                const intersectionPoint = getIntersectionPoint(
                    Math.ceil(ERASER_FIELD_DEFAULT_RADIUS / zoom),
                    newPoint,
                    segments.flat()
                );

                if (!intersectionPoint) return;

                setLassoSegment([]);
                setSegments(deleteSegments(intersectionPoint));
            }

            if (mode !== PolygonMode.Eraser) {
                handleIsStartingPointHovered(newPoint);
                setPointerLine(() => [...segments.flat(), ...lassoSegment, newPoint]);
            }
        }),
        [lassoSegment, mode, segments, zoom, setSegments, setMode, handleIsStartingPointHovered]
    );

    return { onPointerDown, onPointerUp, onPointerMove };
};
