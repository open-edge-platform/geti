// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, useRef, useState } from 'react';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { clampBox, clampPointBetweenImage, pointsToRect } from '../../../../core/annotations/math';
import { Point } from '../../../../core/annotations/shapes.interface';
import { runWhen } from '../../../../shared/utils';
import { isLeftButton } from '../../../buttons-utils';
import { getRelativePoint } from '../../../utils';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { Crosshair } from '../crosshair/crosshair.component';
import { useCrosshair } from '../crosshair/utils';
import { SvgToolCanvas } from '../svg-tool-canvas.component';
import { PointerType } from '../tools.interface';

const CURSOR_OFFSET = '7 8';

interface CrosshairDrawingBoxProps {
    onStart: () => void;
    onMove: (box: RegionOfInterest) => void;
    onComplete: () => void;
    zoom: number;
}

const isLeftClickNonTouch = (event: PointerEvent<SVGSVGElement>) => {
    return isLeftButton(event) && event.pointerType !== PointerType.Touch;
};

const onLeftClick = runWhen(isLeftClickNonTouch);

export const CrosshairDrawingBox = ({ onStart, onMove, onComplete, zoom }: CrosshairDrawingBoxProps): JSX.Element => {
    const { roi, image } = useROI();

    const ref = useRef<SVGRectElement>(null);
    const crosshair = useCrosshair(ref, zoom);
    const [startPoint, setStartPoint] = useState<Point | null>(null);

    const clampPoint = clampPointBetweenImage(image);

    const onPointerDown = onLeftClick((event: PointerEvent<SVGSVGElement>): void => {
        if (startPoint !== null || ref.current === null) {
            return;
        }

        event.currentTarget.setPointerCapture(event.pointerId);

        const newPoint = getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom);
        onStart();
        setStartPoint(clampPoint(newPoint));
    });

    const onPointerMove = (event: PointerEvent<SVGSVGElement>): void => {
        crosshair.onPointerMove(event);

        if (ref.current === null || startPoint === null || !event.currentTarget.hasPointerCapture(event.pointerId)) {
            return;
        }

        const endPoint = clampPoint(getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom));

        onMove(clampBox(pointsToRect(startPoint, endPoint), roi));
    };

    const onPointerUp = onLeftClick((event: PointerEvent<SVGSVGElement>): void => {
        setStartPoint(null);
        onComplete();

        event.currentTarget.releasePointerCapture(event.pointerId);
    });

    return (
        <SvgToolCanvas
            image={image}
            canvasRef={ref}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerLeave={crosshair.onPointerLeave}
            style={{ cursor: `url(/icons/cursor/selection.svg) ${CURSOR_OFFSET}, auto` }}
        >
            <Crosshair location={crosshair.location} zoom={zoom} />
        </SvgToolCanvas>
    );
};
