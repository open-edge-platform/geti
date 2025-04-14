// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { getBoundingBox } from '../../../../core/annotations/math';
import { Rect, Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { Circle } from '../../annotation/shapes/circle.component';
import { Rectangle } from '../../annotation/shapes/rectangle.component';
import { RotatedRectangle } from '../../annotation/shapes/rotated-rectangle.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { DrawingCircle } from '../circle-tool/drawing-circle.component';
import { DrawingBox } from '../drawing-box/drawing-box.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles } from '../utils';
import { useSSIMState } from './ssim-state-provider.component';
import { convertRectToShape } from './util';

import classes from './ssim-tool.module.scss';

export const SSIMTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { defaultLabel } = useTask();
    const { scene, getToolSettings } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();
    const { roi, image } = useROI();

    const { runSSIM, toolState, previewThreshold } = useSSIMState();

    const ssimSettings = getToolSettings(ToolType.SSIMTool);

    const styles = drawingStyles(defaultLabel);

    const [circleRadius, setCircleRadius] = useState<number>(20);

    const { autoMergeDuplicates, shapeType } = ssimSettings;

    const currentAnnotations = scene.annotations;

    const handleShapeDrawn = (shape: Shape) => {
        const templateArea = getBoundingBox(shape);
        const template: Rect = {
            shapeType: ShapeType.Rect,
            x: templateArea.x - roi.x,
            y: templateArea.y - roi.y,
            width: templateArea.width,
            height: templateArea.height,
        };

        runSSIM({
            imageData: image,
            roi,
            template,
            existingAnnotations: currentAnnotations.map((val) => val.shape),
            autoMergeDuplicates,
            shapeType,
        });
    };

    const shapeFactory = (shape: Shape, index: number) => {
        const isTemplate = index === 0;
        const className = isTemplate ? classes.sourceArea : '';
        const ariaLabel = isTemplate ? 'template' : 'prediction';

        switch (shape.shapeType) {
            case ShapeType.Rect:
                return (
                    <Rectangle
                        key={`shape-${index}`}
                        shape={shape}
                        ariaLabel={ariaLabel}
                        styles={{ ...styles, role: 'application', className }}
                    />
                );
            case ShapeType.RotatedRect:
                return (
                    <RotatedRectangle
                        key={`shape-${index}`}
                        shape={shape}
                        ariaLabel={ariaLabel}
                        styles={{ ...styles, role: 'application', className }}
                    />
                );
            case ShapeType.Circle:
                return (
                    <Circle
                        shape={shape}
                        key={`shape-${index}`}
                        ariaLabel={ariaLabel}
                        styles={{ ...styles, role: 'application', className }}
                    />
                );
            default:
                return <></>;
        }
    };

    const previewShapes = (threshold: number): Shape[] => {
        return toolState.matches.slice(0, threshold).map(({ shape }) => convertRectToShape(shape, shapeType));
    };

    const shapes = previewThreshold === null ? toolState.shapes : previewShapes(previewThreshold);

    return (
        <>
            <svg>{shapes.map((shape, index) => shapeFactory(shape, index))}</svg>

            {shapeType === ShapeType.Rect && (
                <DrawingBox image={image} onComplete={handleShapeDrawn} styles={styles} zoom={zoom} />
            )}

            {shapeType === ShapeType.Circle && (
                <DrawingCircle
                    image={image}
                    onComplete={handleShapeDrawn}
                    updateRadius={setCircleRadius}
                    styles={styles}
                    zoom={zoom}
                    defaultRadius={circleRadius}
                />
            )}
        </>
    );
};
