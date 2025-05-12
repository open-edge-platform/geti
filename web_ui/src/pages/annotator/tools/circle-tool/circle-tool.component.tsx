// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Circle } from '../../../../core/annotations/shapes.interface';
import { CircleSizePreview } from '../../components/circle-size-preview/circle-size-preview.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { isCenterOfShapeWithinROI } from '../geometry-utils';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles } from '../utils';
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
        isCenterOfShapeWithinROI(roi, circle) && scene.addShapes([circle]);
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
