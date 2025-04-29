// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { PoseKeypoint } from '../../../../annotator/annotation/shapes/pose-keypoints.component';
import { ResizeAnchor } from '../../../../annotator/tools/edit-tool/resize-anchor.component';
import { ResizeAnchorType } from '../../../../annotator/tools/edit-tool/resize-anchor.enum';

interface PointsProps {
    zoom: number;
    points: KeypointNode[];
    cursor: string;
    onStart: (point: KeypointNode) => void;
    onMove: (point: KeypointNode, index: number) => void;
    onComplete: (point: KeypointNode, index: number) => void;
}

export const Points = ({ zoom, points, cursor, onStart, onMove, onComplete }: PointsProps) => {
    return points.map((point, index) => {
        return (
            <ResizeAnchor
                key={point.label.id}
                y={point.y}
                x={point.x}
                zoom={zoom}
                cursor={cursor}
                label={`keypoint ${point.label.name} anchor`}
                type={ResizeAnchorType.CUSTOM}
                Anchor={<PoseKeypoint point={point} aria-label={`keypoint ${point.label.name} circle`} />}
                onStart={() => onStart(point)}
                onComplete={() => onComplete(point, index)}
                moveAnchorTo={(x, y) => onMove({ ...point, x, y }, index)}
            />
        );
    });
};
