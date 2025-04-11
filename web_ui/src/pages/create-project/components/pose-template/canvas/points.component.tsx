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
