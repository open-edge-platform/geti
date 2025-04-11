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

import { PointerEventHandler, useRef, useState } from 'react';

import flow from 'lodash/flow';
import isEmpty from 'lodash/isEmpty';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Point, Polygon } from '../../../../../core/annotations/shapes.interface';
import { getTheTopShapeAt } from '../../../../../core/annotations/utils';
import { hasDifferentId, runWhen } from '../../../../../shared/utils';
import { CircleSizePreview } from '../../../components/circle-size-preview/circle-size-preview.component';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { getOutputFromTask } from '../../../providers/task-chain-provider/utils';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { pointsToCircle } from '../../circle-tool/utils';
import { PolygonDraw } from '../../polygon-draw.component';
import { SvgToolCanvas } from '../../svg-tool-canvas.component';
import {
    drawingStyles,
    getShapesDifference,
    getShapesUnion,
    isPolygonValid,
    removeOffLimitPointsPolygon,
} from '../../utils';
import { BrushToolProps, GhostPolygon } from '../selecting.interface';
import { calcRelativePoint, getSelectedPolygonAnnotations } from '../utils';
import { BrushCircleTool } from './brush-circle-tool.component';

import classes from '../selecting-tool.module.scss';

const getGhostPolygon = (polygon: GhostPolygon | null, annotation: Annotation): GhostPolygon => {
    if (!polygon?.shape) {
        return { shape: annotation?.shape as Polygon, annotationId: annotation?.id };
    }
    if (polygon && polygon.annotationId === annotation?.id) {
        return { ...polygon };
    }
    return { shape: annotation?.shape as Polygon, annotationId: annotation?.id };
};

export const BrushTool = ({ annotationToolContext, brushSize, showCirclePreview }: BrushToolProps): JSX.Element => {
    const { tasks, selectedTask } = useTask();
    const { scene } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();

    const ref = useRef<SVGRectElement>(null);
    const { roi, image } = useROI();
    const [isPointerDown, setIsPointerDown] = useState(false);
    const [isInsidePolygon, setIsInsidePolygon] = useState(false);
    const [ghostPolygon, setGhostPolygon] = useState<GhostPolygon | null>(null);

    const [selectedPolygonAnnotation] = getSelectedPolygonAnnotations(
        getOutputFromTask(scene.annotations, tasks, selectedTask) as Annotation[]
    );

    const relativePoint = calcRelativePoint(zoom, ref);

    const onPointerDown: PointerEventHandler<SVGSVGElement> = (event) => {
        event.currentTarget.setPointerCapture(event.pointerId);

        if (Boolean(selectedPolygonAnnotation?.id)) {
            relativePoint((point: Point) => {
                const annotation = getTheTopShapeAt([selectedPolygonAnnotation], point);
                setIsInsidePolygon(selectedPolygonAnnotation?.id === annotation?.id);
                setIsPointerDown(true);
            })(event);
        }
    };

    const updateGhostPolygon = relativePoint((point: Point): Annotation => {
        const circleShape = pointsToCircle(point, point, brushSize);

        const shapeHandler = isInsidePolygon ? getShapesUnion : getShapesDifference;
        const newGhostPolygon = getGhostPolygon(ghostPolygon, selectedPolygonAnnotation);

        const solutionShape = shapeHandler(roi, newGhostPolygon.shape, circleShape);

        setGhostPolygon({ shape: solutionShape, annotationId: newGhostPolygon.annotationId });

        return selectedPolygonAnnotation;
    });

    const hideAnnotation = runWhen((annotation: Annotation) => !annotation?.isHidden)((annotation): void => {
        // include the annotations outside the current task or them will be removed
        const visibleAnnotations = annotationToolContext.scene.annotations.filter(hasDifferentId(annotation.id));
        //we use replaceAnnotations because it's necessary skip the visible on/off change in the redo/undo history
        scene.replaceAnnotations([...visibleAnnotations, { ...annotation, isHidden: true }], true);
    });

    const onPointerMove = runWhen(() => isPointerDown)(flow([updateGhostPolygon, hideAnnotation]));

    const updateOrRemoveAnnotation = (annotation: Annotation, newShape: Polygon) => {
        if (isPolygonValid(newShape)) {
            scene.updateAnnotation({
                ...annotation,
                isHidden: false,
                shape: removeOffLimitPointsPolygon(newShape, roi),
            });
        } else {
            scene.removeAnnotations([annotation]);
        }
    };

    const onPointerUp: PointerEventHandler<SVGSVGElement> = (event) => {
        event.currentTarget.releasePointerCapture(event.pointerId);

        if (ghostPolygon) {
            updateOrRemoveAnnotation(selectedPolygonAnnotation, ghostPolygon.shape);
            setGhostPolygon(null);
        }

        setIsPointerDown(false);
    };

    return (
        <CircleSizePreview circleSize={brushSize} roi={roi} isCircleSizePreviewVisible={showCirclePreview}>
            <SvgToolCanvas
                canvasRef={ref}
                image={image}
                onPointerDown={onPointerDown}
                onPointerMove={onPointerMove}
                onPointerUp={onPointerUp}
                onMouseLeave={onPointerUp}
            >
                {ghostPolygon && !isEmpty(ghostPolygon?.shape?.points) && (
                    <PolygonDraw
                        ariaLabel='ghostPolygon'
                        className={classes.ghostPolygon}
                        shape={ghostPolygon.shape}
                        styles={drawingStyles(null)}
                    />
                )}
                <BrushCircleTool
                    image={image}
                    zoom={zoom}
                    brushSize={brushSize}
                    isPointerDown={isPointerDown}
                    isInsidePolygon={isInsidePolygon}
                />
            </SvgToolCanvas>
        </CircleSizePreview>
    );
};
