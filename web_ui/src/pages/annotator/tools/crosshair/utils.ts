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
