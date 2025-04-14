// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { KeypointNode, Point } from '../../../../../core/annotations/shapes.interface';
import { allowPanning } from '../../../../annotator/tools/utils';
import { useZoom } from '../../../../annotator/zoom/zoom-provider.component';
import { getRelativePoint, leftMouseButtonHandler } from '../../../../utils';
import { getDefaultLabelStructure } from '../util';

interface DrawingBoxProps {
    totalPoints: number;
    onAddPoint: (point: KeypointNode) => void;
    onPointerMove: (point: Point) => void;
}

export const DrawingBox = ({ totalPoints, onAddPoint, onPointerMove }: DrawingBoxProps) => {
    const canvasRef = useRef<SVGRectElement>(null);
    const { zoomState } = useZoom();

    const onPointerDown = leftMouseButtonHandler((event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
    });

    const onPointerUp = leftMouseButtonHandler((event) => {
        if (canvasRef.current === null) {
            return;
        }

        onAddPoint({
            label: getDefaultLabelStructure(String(totalPoints)),
            isVisible: true,
            ...getRelativePoint(canvasRef.current, { x: event.clientX, y: event.clientY }, zoomState.zoom),
        });

        event.currentTarget.releasePointerCapture(event.pointerId);
    });

    return (
        <rect
            aria-label={'drawing box'}
            width={'100%'}
            height={'100%'}
            fillOpacity={0}
            ref={canvasRef}
            style={{ cursor: 'crosshair' }}
            onPointerUp={allowPanning(onPointerUp)}
            onPointerDown={allowPanning(onPointerDown)}
            onPointerMove={({ clientX, clientY }) => {
                if (!canvasRef.current) {
                    return;
                }

                onPointerMove(getRelativePoint(canvasRef.current, { x: clientX, y: clientY }, zoomState.zoom));
            }}
        />
    );
};
