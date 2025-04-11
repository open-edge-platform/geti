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

import { Virtuoso } from 'react-virtuoso';

import { KeypointAnnotation } from '../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { HeightPreservingItem } from '../height-preserving-item.component';
import { NodeContent } from './node-content.component';

interface NodeListProps {
    keypointAnnotation: KeypointAnnotation;
}

export const NodeList = ({ keypointAnnotation }: NodeListProps) => {
    const { updateAnnotation } = useAnnotationScene();

    const points = [...keypointAnnotation.shape.points].reverse();

    const handleUpdateAnnotation = (newPoint: KeypointNode) => {
        updateAnnotation({
            ...keypointAnnotation,
            shape: {
                shapeType: ShapeType.Pose,
                points: keypointAnnotation.shape.points.map((currentPoint) =>
                    currentPoint.label.id === newPoint.label.id ? newPoint : currentPoint
                ),
            },
        });
    };

    return (
        <Virtuoso<KeypointNode>
            id={'keypoint-list'}
            role={'list'}
            data={points}
            aria-label={'keypoint list'}
            components={{ Item: HeightPreservingItem }}
            itemContent={(index, point) => (
                <NodeContent point={point} isLast={index === points.length - 1} onUpdate={handleUpdateAnnotation} />
            )}
        />
    );
};
