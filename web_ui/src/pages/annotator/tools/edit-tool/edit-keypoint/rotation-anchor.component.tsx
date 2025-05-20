// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Rotation } from '@geti/ui/icons';
import clsx from 'clsx';

import { radiansToDegrees } from '../../../../../core/annotations/math';
import { Point } from '../../../../../core/annotations/shapes.interface';
import * as Vec2 from '../../../../../core/annotations/vec2';
import { Anchor } from '../anchor.component';

import styles from './rotation-anchor.module.scss';

export interface RotationAnchorProps {
    size: number;
    zoom: number;
    pivot: Point;
    position: Point;
    basePosition: Point;
    onComplete: () => void;
    onMoveAnchorTo: (angle: number) => void;
}

export const RotationAnchor = ({
    pivot,
    zoom,
    size,
    position,
    basePosition,
    onComplete,
    onMoveAnchorTo,
}: RotationAnchorProps) => {
    const anchorSize = size / zoom;
    const anchorVector = Vec2.sub(position, pivot);

    const handleMoveAnchor = (x: number, y: number) => {
        const pivotVector = Vec2.sub({ x, y }, pivot);
        const radians = Math.atan2(pivotVector.y, pivotVector.x) - Math.atan2(anchorVector.y, anchorVector.x);
        const angle = radiansToDegrees(radians);

        onMoveAnchorTo(angle > 0 ? angle : angle + 360);
    };

    return (
        <>
            {[styles.whiteDash, styles.blackDash].map((color, index) => (
                <line
                    key={`dashed-line-${index}`}
                    className={clsx(styles.line, color)}
                    x1={position.x}
                    y1={position.y}
                    x2={basePosition.x}
                    y2={basePosition.y}
                />
            ))}

            <Anchor
                zoom={zoom}
                size={anchorSize}
                x={position.x}
                y={position.y}
                label={'rotate anchor'}
                cursor={'url(/icons/cursor/rotate.svg) 7 8, auto'}
                onComplete={onComplete}
                moveAnchorTo={handleMoveAnchor}
            >
                <>
                    <rect
                        fill='var(--spectrum-global-color-gray-100)'
                        stroke='white'
                        width={anchorSize * 1.6}
                        height={anchorSize * 1.6}
                        strokeWidth={1 / zoom}
                        x={position.x - anchorSize / 1.2}
                        y={position.y - anchorSize / 1.2}
                    />
                    <Rotation
                        width={anchorSize}
                        height={anchorSize}
                        x={position.x - anchorSize / 2}
                        y={position.y - anchorSize / 2}
                    />
                </>
            </Anchor>
        </>
    );
};
