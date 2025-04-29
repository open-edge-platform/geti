// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef, useState } from 'react';

import { Circle as CircleInterface, Point } from '../../../../../core/annotations/shapes.interface';
import { runWhen } from '../../../../../shared/utils';
import { Circle } from '../../../annotation/shapes/circle.component';
import { pointsToCircle } from '../../circle-tool/utils';
import { SvgToolCanvas } from '../../svg-tool-canvas.component';
import { drawingStyles, SELECT_ANNOTATION_STYLES } from '../../utils';
import { CURSOR_OFFSET, MINUS_OFFSET } from '../../watershed-tool/utils';
import { calcRelativePoint } from '../utils';

interface BrushCircleToolProps {
    zoom: number;
    brushSize: number;
    isPointerDown: boolean;
    isInsidePolygon: boolean;
    image: ImageData;
}

export const BrushCircleTool = ({
    zoom,
    image,
    brushSize,
    isPointerDown = false,
    isInsidePolygon = false,
}: BrushCircleToolProps): JSX.Element => {
    const ref = useRef<SVGRectElement>(null);
    const [circle, setCircle] = useState<CircleInterface | null>(null);
    const [isActive, setIsActive] = useState(false);

    const relativePoint = calcRelativePoint(zoom, ref);

    const onCircleMove = relativePoint((point: Point): void => setCircle(pointsToCircle(point, point, brushSize)));

    const onPointerDown = runWhen(() => Boolean(circle))(() => {
        setIsActive(true);
    });

    const onPointerUp = runWhen(() => isActive)(() => {
        setIsActive(false);
    });

    const getCursor = (): { cursor: string } => {
        if (isPointerDown) {
            return isInsidePolygon
                ? { cursor: `url(/icons/cursor/plus.svg) ${MINUS_OFFSET}, auto` }
                : { cursor: `url(/icons/cursor/minus.svg) ${MINUS_OFFSET}, auto` };
        }

        return { cursor: `url(/icons/cursor/circle.svg) ${CURSOR_OFFSET}, auto` };
    };

    return (
        <SvgToolCanvas
            canvasRef={ref}
            image={image}
            onPointerDown={onPointerDown}
            onPointerUp={onPointerUp}
            onPointerMove={onCircleMove}
            onMouseLeave={() => {
                setCircle(null);
                onPointerUp();
            }}
            style={getCursor()}
        >
            {circle && <Circle shape={circle} styles={isActive ? SELECT_ANNOTATION_STYLES : drawingStyles(null)} />}
        </SvgToolCanvas>
    );
};
