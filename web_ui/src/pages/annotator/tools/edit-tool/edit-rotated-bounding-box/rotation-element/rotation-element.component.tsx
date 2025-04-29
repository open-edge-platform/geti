// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { RegionOfInterest } from '../../../../../../core/annotations/annotation.interface';
import { radiansToDegrees } from '../../../../../../core/annotations/math';
import { RotatedRect } from '../../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../../core/annotations/shapetype.enum';
import * as Vec2 from '../../../../../../core/annotations/vec2';
import { Line } from '../../../../annotation/shapes/line.component';
import { SideAnchorLocationsProps } from '../location';
import { RotationAnchor } from './rotation-anchor.component';
import { Direction, getDirection } from './utils';

interface RotationElementProps {
    zoom: number;
    onComplete: () => void;
    shape: RotatedRect & { shapeType: ShapeType.RotatedRect };
    setShape: (shape: RotatedRect & { shapeType: ShapeType.RotatedRect }) => void;
    sideAnchorLocations: SideAnchorLocationsProps;
    roi: RegionOfInterest;
}

export const RotationElement = ({
    zoom,
    onComplete,
    shape,
    setShape,
    sideAnchorLocations,
    roi,
}: RotationElementProps): JSX.Element => {
    const [isRotating, setIsRotating] = useState<boolean>(false);
    const [rotationDirection, setRotationDirection] = useState<Direction>(getDirection(sideAnchorLocations, roi));
    const shapePosition = { x: shape.x, y: shape.y };

    useEffect(() => {
        if (!isRotating) {
            setRotationDirection(getDirection(sideAnchorLocations, roi));
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shape, isRotating]);

    const rotationAnchorLocation = sideAnchorLocations.withGap[rotationDirection];
    const rotationAnchorLineEnd =
        rotationDirection !== Direction.MIDDLE ? sideAnchorLocations.lineEnd[rotationDirection] : undefined;
    const rotationAnchorLineStart = sideAnchorLocations[rotationDirection];
    const rotationAnchor = {
        ...rotationAnchorLocation,
        moveAnchorTo: (x: number, y: number) => {
            setIsRotating(true);

            const anchorToCenter = Vec2.sub({ x, y }, shapePosition);
            const baseVector = sideAnchorLocations.baseVector[rotationDirection];
            const radians = Math.atan2(anchorToCenter.y, anchorToCenter.x) - Math.atan2(baseVector.y, baseVector.x);
            const angle = radiansToDegrees(radians);

            setShape({
                ...shape,
                angle: angle > 0 ? angle : angle + 360,
            });
        },
        cursor: 'url(/icons/cursor/rotate.svg) 7 8, auto',
        label: 'Rotate anchor',
    };

    const onCompleteHandler = () => {
        setIsRotating(false);
        onComplete();
    };

    return (
        <>
            {rotationAnchorLineEnd && !isRotating && (
                <Line
                    brushSize={2 / zoom}
                    color={'var(--energy-blue)'}
                    points={[rotationAnchorLineStart, rotationAnchorLineEnd]}
                />
            )}
            <RotationAnchor
                isRotating={isRotating}
                angle={shape.angle}
                key={rotationAnchor.label}
                zoom={zoom}
                onComplete={onCompleteHandler}
                {...rotationAnchor}
            />
        </>
    );
};
