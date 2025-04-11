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

import { Circle } from '../../../../core/annotations/shapes.interface';
import { CircleSizePreview } from '../../components/circle-size-preview/circle-size-preview.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles, isShapeWithinRoi } from '../utils';
import { useCircleState } from './circle-state-provider.component';
import { DrawingCircle } from './drawing-circle.component';

export const CircleTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { defaultLabel } = useTask();
    const { scene, updateToolSettings } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();
    const { roi, image } = useROI();
    const styles = drawingStyles(defaultLabel);
    const { isBrushSizePreviewVisible, circleRadiusSize, setCircleRadiusSize, maxCircleRadius } = useCircleState();

    const updateRadius = (size: number) => {
        updateToolSettings(ToolType.CircleTool, { size });
        setCircleRadiusSize(size);
    };

    const onComplete = (circle: Circle) => {
        isShapeWithinRoi(roi, circle) && scene.addShapes([circle]);
    };

    return (
        <CircleSizePreview
            circleSize={circleRadiusSize}
            roi={roi}
            isCircleSizePreviewVisible={isBrushSizePreviewVisible}
        >
            <DrawingCircle
                zoom={zoom}
                image={image}
                styles={styles}
                onComplete={onComplete}
                updateRadius={updateRadius}
                defaultRadius={circleRadiusSize}
                maxCircleRadius={maxCircleRadius}
            />
        </CircleSizePreview>
    );
};
