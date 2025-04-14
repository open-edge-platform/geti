// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { Circle } from './circle.component';
import { Polygon } from './polygon.component';
import { PoseEdges } from './pose-edges.component';
import { PoseKeypoints } from './pose-keypoints.component';
import { Rectangle } from './rectangle.component';
import { RotatedRectangle } from './rotated-rectangle.component';

export const ShapeFactory = ({
    annotation,
}: {
    annotation: Pick<Annotation, 'shape' | 'id' | 'isSelected'> & Partial<Annotation>;
}): JSX.Element => {
    const { shape, id, isSelected } = annotation;

    const ariaLabel = `${isSelected ? 'Selected' : 'Not selected'} shape ${id}`;

    switch (shape.shapeType) {
        case ShapeType.Rect:
            return <Rectangle shape={shape} ariaLabel={ariaLabel} />;
        case ShapeType.RotatedRect:
            return <RotatedRectangle shape={shape} ariaLabel={ariaLabel} />;
        case ShapeType.Circle:
            return <Circle shape={shape} ariaLabel={ariaLabel} />;
        case ShapeType.Polygon:
            return <Polygon shape={shape} ariaLabel={ariaLabel} />;
        case ShapeType.Pose:
            return (
                <g strokeLinecap={'butt'}>
                    <PoseEdges shape={shape} showBoundingBox={false} />
                    <PoseKeypoints shape={shape} ariaLabel={ariaLabel} />;
                </g>
            );
    }
};
