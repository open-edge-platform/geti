// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
