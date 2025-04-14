// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
