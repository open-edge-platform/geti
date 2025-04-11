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

import { PointerEvent, SVGProps, useCallback, useRef, useState } from 'react';

import { calculateDistance } from '../../../../core/annotations/math';
import { Circle as CircleInterface, Point } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { KeyboardEvents } from '../../../../shared/keyboard-events/keyboard.interface';
import { onEscape } from '../../../../shared/utils';
import { isEraserButton, isLeftButton, isRightButton } from '../../../buttons-utils';
import { getRelativePoint } from '../../../utils';
import { Circle } from '../../annotation/shapes/circle.component';
import { SvgToolCanvas } from '../svg-tool-canvas.component';
import { PointerType } from '../tools.interface';
import { EDIT_SIZE_ANNOTATION_STYLES } from '../utils';
import { MIN_RADIUS, Mode, pointsToCircle } from './utils';

interface DrawingCircleInterface {
    onComplete: (shapes: CircleInterface) => void;
    image: ImageData;
    zoom: number;
    defaultRadius: number;
    updateRadius?: (radius: number) => void;
    maxCircleRadius?: number;
    styles: SVGProps<SVGCircleElement>;
}

export const DrawingCircle = ({
    onComplete,
    image,
    zoom,
    defaultRadius,
    updateRadius,
    maxCircleRadius,
    styles,
}: DrawingCircleInterface): JSX.Element => {
    const ref = useRef<SVGRectElement>(null);

    const [startPoint, setStartPoint] = useState<Point | null>(null);
    const [circle, setCircle] = useState<CircleInterface | null>(null);
    const [mode, setMode] = useState<Mode>(Mode.NORMAL);

    const [stampModeIsEnabled, setStampModeIsEnabled] = useState(true);

    const onPointerMove = useCallback(
        (event: PointerEvent<SVGSVGElement>): void => {
            if (ref.current === null) {
                return;
            }

            const button = {
                button: event.button,
                buttons: event.buttons,
            };

            if (event.pointerType === PointerType.Pen && isEraserButton(button)) {
                setCleanState();

                return;
            }

            const mousePoint = getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom);

            if (startPoint === null) {
                setCircle({ x: mousePoint.x, y: mousePoint.y, r: defaultRadius, shapeType: ShapeType.Circle });
            } else {
                const radius = calculateDistance(startPoint, mousePoint);

                if (maxCircleRadius !== undefined && radius > maxCircleRadius) {
                    return;
                }

                if (stampModeIsEnabled && radius > defaultRadius) {
                    setStampModeIsEnabled(false);
                }

                const newCircle = pointsToCircle(
                    startPoint,
                    mousePoint,
                    stampModeIsEnabled ? defaultRadius : MIN_RADIUS
                );

                setCircle(newCircle);
            }
        },
        [startPoint, zoom, defaultRadius, stampModeIsEnabled, maxCircleRadius]
    );

    const onPointerDown = useCallback(
        (event: PointerEvent<SVGSVGElement>): void => {
            if (startPoint !== null || ref.current === null) {
                return;
            }

            const button = {
                button: event.button,
                buttons: event.buttons,
            };

            if (event.pointerType === PointerType.Touch || (!isLeftButton(button) && !isRightButton(button))) {
                return;
            }

            if (isRightButton(button)) {
                setMode(Mode.EDIT_RADIUS);
            }

            event.currentTarget.setPointerCapture(event.pointerId);

            const mouse = getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom);

            setStartPoint(mouse);
            setCircle({ x: mouse.x, y: mouse.y, r: defaultRadius, shapeType: ShapeType.Circle });
        },
        [startPoint, zoom, defaultRadius]
    );

    const onPointerUp = useCallback(
        (event: PointerEvent<SVGSVGElement>): void => {
            if (event.pointerType === PointerType.Touch) {
                return;
            }

            if (circle === null) {
                return;
            }

            // Don't make empty annotations
            if (circle.r >= MIN_RADIUS && startPoint !== null) {
                onComplete({ ...circle });

                if (mode === Mode.EDIT_RADIUS) {
                    if (updateRadius) {
                        updateRadius(circle.r);
                    }
                    setMode(Mode.NORMAL);
                }
            }

            setCleanState();

            event.currentTarget.releasePointerCapture(event.pointerId);
        },
        [circle, mode, onComplete, startPoint, updateRadius]
    );

    const setCleanState = () => {
        setStartPoint(null);
        setCircle(null);
        setMode(Mode.NORMAL);
        setStampModeIsEnabled(true);
    };

    useEventListener(
        KeyboardEvents.KeyDown,
        onEscape(() => setCleanState())
    );

    const circleStyles = mode === Mode.EDIT_RADIUS ? EDIT_SIZE_ANNOTATION_STYLES : styles;

    return (
        <SvgToolCanvas
            image={image}
            canvasRef={ref}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerMove}
        >
            {circle ? (
                <Circle
                    ariaLabel='Circle tool canvas'
                    shape={circle}
                    styles={{ ...circleStyles, role: 'application' }}
                />
            ) : null}
        </SvgToolCanvas>
    );
};
