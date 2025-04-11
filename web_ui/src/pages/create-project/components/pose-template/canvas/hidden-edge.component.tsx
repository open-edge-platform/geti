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

import { PointerEvent, useRef, useState } from 'react';

import { usePress } from '@react-aria/interactions';
import clsx from 'clsx';

import { KeypointNode, Point } from '../../../../../core/annotations/shapes.interface';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { PoseKeypoint } from '../../../../annotator/annotation/shapes/pose-keypoints.component';
import { useZoom } from '../../../../annotator/zoom/zoom-provider.component';
import { getRelativePoint, projectPointOnLine } from '../../../../utils';

import classes from './edge.module.scss';

export interface HiddenEdgeProps {
    to: KeypointNode;
    from: KeypointNode;
    isSelected: boolean;
    isHovered: boolean;
    onSelect: (isSelected: boolean) => void;
    onNewIntermediatePoint: (newPoint: Point, prevFrom: KeypointNode, prevTo: KeypointNode) => void;
}

export const HiddenEdge = ({ to, from, isHovered, isSelected, onSelect, onNewIntermediatePoint }: HiddenEdgeProps) => {
    const { zoomState } = useZoom();
    const containerRef = useRef<SVGRectElement>(null);
    const [ghostPoint, setGhostPoint] = useState<Point | null>(null);

    const { pressProps } = usePress({
        onPress: () => {
            if (ghostPoint) {
                onNewIntermediatePoint(ghostPoint, from, to);
            } else {
                onSelect(isSelected);
            }
        },
    });

    if (!isHovered && ghostPoint !== null) {
        setGhostPoint(null);
    }

    const handlePointerMove = (event: PointerEvent) => {
        if (containerRef?.current === null) {
            return;
        }

        const relativePoint = getRelativePoint(
            containerRef.current,
            { x: event.clientX, y: event.clientY },
            zoomState.zoom
        );

        const pointOnLine = projectPointOnLine([from, to], relativePoint);

        pointOnLine && setGhostPoint({ ...pointOnLine });
    };

    return (
        <>
            <rect width='100%' height='100%' fill='none' ref={containerRef} />
            <line
                {...pressProps}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                onPointerMove={isSelected ? handlePointerMove : undefined}
                aria-label={`hidden padded edge ${from.label.name} - ${to.label.name}`}
                className={clsx({
                    [classes.edge]: true,
                    [classes.hiddenEdge]: true,
                    [classes.ghostPoint]: ghostPoint !== null,
                })}
            />

            {ghostPoint && (
                <PoseKeypoint
                    radius={4}
                    fill='var(--spectrum-global-color-gray-900)'
                    point={getMockedKeypointNode(ghostPoint)}
                    aria-label={`ghost keypoint`}
                    style={{ pointerEvents: 'none' }}
                />
            )}
        </>
    );
};
