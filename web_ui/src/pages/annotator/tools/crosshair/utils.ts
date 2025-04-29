// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, RefObject, useState } from 'react';

import { Point } from '../../../../core/annotations/shapes.interface';
import { getRelativePoint } from '../../../utils';

interface UseCrosshair {
    location: Point | null;
    onPointerMove: (event: PointerEvent<SVGSVGElement>) => void;
    onPointerLeave: (event: PointerEvent<SVGSVGElement>) => void;
}

export const useCrosshair = (canvasRef: RefObject<SVGRectElement>, zoom: number): UseCrosshair => {
    const [location, setLocation] = useState<Point | null>(null);

    const onPointerMove = (event: PointerEvent<SVGSVGElement>) => {
        if (canvasRef.current === null) {
            return;
        }

        const newLocation = getRelativePoint(canvasRef.current, { x: event.clientX, y: event.clientY }, zoom);

        setLocation(newLocation);
    };

    const onPointerLeave = (_event: PointerEvent<SVGSVGElement>) => {
        setLocation(null);
    };

    return { location, onPointerMove, onPointerLeave };
};
