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

import { SVGProps } from 'react';

import { CloseBold } from '../../../../assets/icons';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { KEYPOINT_RADIUS } from '../../../utils';
import { useIsHovered } from '../../providers/hovered-provider/hovered-provider.component';
import { useSelected } from '../../providers/selected-provider/selected-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { KeypointProps } from './shape.interface';

export interface PoseKeypointProps extends SVGProps<SVGCircleElement> {
    point: KeypointNode;
    radius?: number;
}

export const PoseKeypointVisibility = ({ point, radius, ...svgProps }: PoseKeypointProps) => {
    const { zoomState } = useZoom();

    const occludedIconSize = 18 / zoomState.zoom;

    if (!point.isVisible) {
        return (
            <CloseBold
                width={occludedIconSize}
                height={occludedIconSize}
                y={point.y - occludedIconSize / 2}
                x={point.x - occludedIconSize / 2}
                style={{
                    fill: point.label.color,
                    cursor: 'default',
                    stroke: 'var(--spectrum-gray-900)',
                    strokeWidth: 2,
                }}
            />
        );
    }

    return <PoseKeypoint point={point} radius={radius} {...svgProps} />;
};

export const PoseKeypoints = ({ shape, ariaLabel }: KeypointProps) => {
    return (
        <>
            {shape.points.map((point, index) => (
                <PoseKeypointVisibility
                    key={`annotation-${point.label.id}`}
                    point={point}
                    aria-label={`${ariaLabel}-${index}`}
                />
            ))}
        </>
    );
};

export const PoseKeypoint = ({ point, radius = KEYPOINT_RADIUS, ...svgProps }: PoseKeypointProps) => {
    const { zoomState } = useZoom();
    const { isSelected } = useSelected();
    const isPointActive = useIsHovered(point.label.id) || isSelected(point.label.id);

    const strokeWidth = radius * 0.4;
    const widthMultiplier = isPointActive ? 2 : 1;

    return (
        <circle
            r={radius / zoomState.zoom}
            cx={point.x}
            cy={point.y}
            fill={isPointActive ? 'var(--spectrum-gray-900)' : point.label.color}
            stroke={isPointActive ? point.label.color : 'var(--spectrum-gray-900)'}
            strokeWidth={`calc(${strokeWidth * widthMultiplier} / var(--zoom-level))`}
            fillOpacity={'var(--annotation-fill-opacity)'}
            strokeOpacity={'var(--annotation-border-opacity)'}
            {...svgProps}
        />
    );
};
