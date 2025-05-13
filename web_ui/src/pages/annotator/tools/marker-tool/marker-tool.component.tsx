// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, ReactElement, SVGProps, useCallback, useRef, useState } from 'react';

import { isEmpty, isFunction, partial } from 'lodash-es';

import { calculateDistance } from '../../../../core/annotations/math';
import { Point } from '../../../../core/annotations/shapes.interface';
import { isLeftButton } from '../../../buttons-utils';
import { getRelativePoint } from '../../../utils';
import { Line } from '../../annotation/shapes/line.component';
import { SvgToolCanvas } from '../svg-tool-canvas.component';
import { PointerType } from '../tools.interface';
import { isPointWithinRoi } from '../utils';
import { MarkerToolProps } from './marker-tool.interface';

const DEFAULT_STROKE_WIDTH = 1.5;

export const MarkerTool = ({
    roi,
    image,
    zoom,
    label,
    styles,
    markerId,
    brushSize,
    onComplete,
    renderCursor,
    strokeLinecap,
    strokeLinejoin,
}: MarkerToolProps): ReactElement<SVGProps<SVGGElement>> | null => {
    const [points, setPoints] = useState<Point[]>([] as Point[]);
    const [brushCursorPoint, setBrushCursorPoint] = useState<Point>({ x: 0, y: 0 });
    const ref = useRef<SVGRectElement>(null);

    const onPointerDown = useCallback(
        (event: PointerEvent<SVGSVGElement>): void => {
            if (ref.current === null) {
                return;
            }

            const button = {
                button: event.button,
                buttons: event.buttons,
            };

            if (event.pointerType === PointerType.Touch || !isLeftButton(button)) {
                return;
            }

            event.currentTarget.setPointerCapture(event.pointerId);

            const mousePoint = getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom);

            setPoints([{ x: Math.round(mousePoint.x), y: Math.round(mousePoint.y) }]);
        },
        [zoom]
    );

    const onPointerMove = useCallback(
        (event: PointerEvent<SVGSVGElement>) => {
            if (ref.current === null) {
                return;
            }

            const mousePoint = getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom);

            setBrushCursorPoint(() => ({ x: mousePoint.x, y: mousePoint.y }));

            if (isEmpty(points)) {
                return;
            }

            const previousPoint = points[points.length - 1];

            const distance = calculateDistance(previousPoint, mousePoint);

            if (distance >= 1) {
                setPoints((previousPoints) => [
                    ...previousPoints,
                    { x: Math.round(mousePoint.x), y: Math.round(mousePoint.y) },
                ]);
            }
        },
        [points, zoom]
    );

    const onPointerUp = useCallback(
        (event: PointerEvent<SVGSVGElement>): void => {
            // Mousewheel
            if (event.button === 1) {
                return;
            }

            event.currentTarget.setPointerCapture(event.pointerId);
            const validPoints = roi ? points.filter(partial(isPointWithinRoi, roi)) : points;

            if (!isEmpty(validPoints)) {
                onComplete({ id: markerId, points: validPoints, label, brushSize });
            }

            setPoints([]);
            event.currentTarget.releasePointerCapture(event.pointerId);
        },
        [roi, points, onComplete, markerId, label, brushSize]
    );

    return (
        <SvgToolCanvas
            image={image}
            canvasRef={ref}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            style={{ ...styles, opacity: 'var(--markers-opacity)' }}
        >
            <>
                <Line
                    points={points}
                    brushSize={brushSize}
                    color={label.color}
                    strokeLinecap={strokeLinecap}
                    strokeLinejoin={strokeLinejoin}
                />
                {isFunction(renderCursor) &&
                    renderCursor({
                        brushSize,
                        y: brushCursorPoint.y,
                        x: brushCursorPoint.x,
                        fill: label.color,
                        ariaLabel: 'Marker',
                        strokeWidth: DEFAULT_STROKE_WIDTH / zoom,
                    })}
            </>
        </SvgToolCanvas>
    );
};
