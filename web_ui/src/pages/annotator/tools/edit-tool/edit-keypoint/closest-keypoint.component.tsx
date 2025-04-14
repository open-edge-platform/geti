// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
