// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
