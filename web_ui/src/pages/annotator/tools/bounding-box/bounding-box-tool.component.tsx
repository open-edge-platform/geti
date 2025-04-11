// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import partial from 'lodash/partial';

import { rectToRotatedRect } from '../../../../core/annotations/rotated-rect-math';
import { Rect } from '../../../../core/annotations/shapes.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { runWhen } from '../../../../shared/utils';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { DrawingBox } from '../drawing-box/drawing-box.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles, isShapeWithinRoi } from '../utils';

export const BoundingBoxTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { scene } = annotationToolContext;
    const { roi, image } = useROI();
    const { defaultLabel, activeDomains } = useTask();
    const isValidRect = partial(isShapeWithinRoi, roi);

    const onComplete = runWhen<Rect>(isValidRect)((shape: Rect) => {
        const isRotatedBoundingBox = activeDomains.includes(DOMAIN.DETECTION_ROTATED_BOUNDING_BOX);
        const rect = isRotatedBoundingBox ? rectToRotatedRect(shape) : shape;
        scene.addShapes([rect]);
    });

    const {
        zoomState: { zoom },
    } = useZoom();

    const styles = drawingStyles(defaultLabel);

    return <DrawingBox onComplete={onComplete} image={image} zoom={zoom} styles={styles} />;
};
