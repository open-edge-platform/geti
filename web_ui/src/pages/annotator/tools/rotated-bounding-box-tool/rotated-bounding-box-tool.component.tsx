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

import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles } from '../utils';
import { RotatedDrawingBox } from './rotated-drawing-box.component';

export const RotatedBoundingBoxTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { defaultLabel } = useTask();
    const { scene } = annotationToolContext;
    const { image } = useROI();
    const onComplete = scene.addShapes;
    const {
        zoomState: { zoom },
    } = useZoom();

    const styles = drawingStyles(defaultLabel);

    return <RotatedDrawingBox onComplete={onComplete} image={image} zoom={zoom} styles={styles} />;
};
