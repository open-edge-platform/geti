// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { HTMLProps, PointerEvent, ReactNode, useRef, useState } from 'react';

import isFunction from 'lodash/isFunction';

import { calculateDistance } from '../../../../../core/annotations/math';
import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { getRelativePoint } from '../../../../utils';
import { useZoom } from '../../../zoom/zoom-provider.component';

interface ClosestPointProps extends Omit<HTMLProps<SVGSVGElement>, 'children'> {
    nodes: KeypointNode[];
    children: ReactNode | ((element: KeypointNode | null) => ReactNode);
    onClosestElement?: (element: KeypointNode) => void;
}

export const ClosestKeypoint = ({ children, nodes, onClosestElement, ...svgProps }: ClosestPointProps) => {
    const { zoomState } = useZoom();
    const containerRef = useRef<SVGSVGElement | null>(null);
    const [closestElement, setClosestElement] = useState<KeypointNode | null>(null);

    const handlePointerMove = ({ clientX, clientY }: PointerEvent<SVGSVGElement>) => {
        if (containerRef.current == null) {
            return;
        }

        let minDistance = Infinity;
        let localClosestElement: KeypointNode | undefined;
        const relativePoint = getRelativePoint(containerRef.current, { x: clientX, y: clientY }, zoomState.zoom);

        nodes.forEach((node) => {
            const distance = calculateDistance(relativePoint, node);

            if (distance < minDistance) {
                minDistance = distance;
                localClosestElement = node;
            }
        });

        if (localClosestElement) {
            setClosestElement(localClosestElement);
            isFunction(onClosestElement) && onClosestElement(localClosestElement);
        }
    };

    return (
        <svg {...svgProps} ref={containerRef} onPointerMove={handlePointerMove}>
            {isFunction(children) ? children(closestElement) : children}
        </svg>
    );
};
