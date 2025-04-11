// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
