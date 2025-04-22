// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef, useState } from 'react';

import { KeypointAnnotation } from '../../../../../core/annotations/annotation.interface';
import { getBoundingBox } from '../../../../../core/annotations/math';
import { Point } from '../../../../../core/annotations/shapes.interface';
import { PoseEdges } from '../../../annotation/shapes/pose-edges.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useSelected } from '../../../providers/selected-provider/selected-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import {
    getAnnotationInBoundingBox,
    getInnerPaddedBoundingBox,
    getOuterPaddedBoundingBox,
    getPoseLocations,
    MIN_BOUNDING_BOX_SIZE,
    rotatePointsAroundPivot,
} from '../../keypoint-tool/utils';
import { ANCHOR_SIZE, ResizeAnchor } from '../resize-anchor.component';
import { TranslateShape } from '../translate-shape.component';
import { getBoundingBoxInRoi, getBoundingBoxResizePoints, getClampedBoundingBox } from '../utils';
import { ClosestKeypoint } from './closest-keypoint.component';
import { EditPosePoint } from './edit-pose-point.component';
import { RotationAnchor } from './rotation-anchor.component';
import { toggleVisibility, updatePoint } from './util';

import classes from './../../../annotator-canvas.module.scss';

interface EditKeypointToolProps {
    annotation: KeypointAnnotation;
    annotationToolContext: AnnotationToolContext;
}

export const EditKeypointTool = ({ annotation, annotationToolContext }: EditKeypointToolProps) => {
    const isEditing = useRef(false);
    const { zoomState } = useZoom();
    const { image, roi } = useROI();
    const { isSelected, setSelected, removeSelected } = useSelected();
    const [angle, setAngle] = useState(0);

    const [localShape, setLocalShape] = useState(annotation.shape);
    const [paddedLocalBoundingBox, setPaddedLocalBoundingBox] = useState(
        getOuterPaddedBoundingBox(getBoundingBox(annotation.shape), zoomState.zoom)
    );

    const rotateAnchorGap = (4 * ANCHOR_SIZE) / zoomState.zoom;
    const poseLocations = getPoseLocations(localShape.points, rotateAnchorGap);

    useEffect(() => {
        if (isEditing.current) {
            isEditing.current = false;
            return;
        }
        // handle undo/redo renderings
        setLocalShape(annotation.shape);
        setPaddedLocalBoundingBox(getOuterPaddedBoundingBox(getBoundingBox(annotation.shape), zoomState.zoom));
    }, [annotation.shape, zoomState.zoom]);

    const handleMovePointByIndex = (idx: number) => (x: number, y: number) => {
        const newShape = {
            ...localShape,
            points: updatePoint(localShape.points, idx, { x, y }),
        };

        setLocalShape(newShape);
        setPaddedLocalBoundingBox(getOuterPaddedBoundingBox(getBoundingBox(newShape), zoomState.zoom));
    };

    const handleTranslate = (point: Point) => {
        isEditing.current = true;
        const boundingBoxInRoi = getClampedBoundingBox(point, paddedLocalBoundingBox, roi);
        const innerBoundingBoxInRoi = getInnerPaddedBoundingBox(boundingBoxInRoi, zoomState.zoom);
        const resizedAnnotation = getAnnotationInBoundingBox(annotation.shape.points, innerBoundingBoxInRoi);

        setLocalShape(resizedAnnotation.shape);
        setPaddedLocalBoundingBox(boundingBoxInRoi);
    };

    const handleComplete = (shape = localShape) => {
        annotationToolContext.scene.updateAnnotation({ ...annotation, shape });
    };

    const boundingBoxResizePoints = getBoundingBoxResizePoints({
        gap: MIN_BOUNDING_BOX_SIZE,
        boundingBox: paddedLocalBoundingBox,
        onResized: (boundingBox) => {
            isEditing.current = true;
            const boundingBoxInRoi = getBoundingBoxInRoi(boundingBox, roi);
            const innerBoundingBoxInRoi = getInnerPaddedBoundingBox(boundingBoxInRoi, zoomState.zoom);
            const resizedAnnotation = getAnnotationInBoundingBox(annotation.shape.points, innerBoundingBoxInRoi);

            setLocalShape(resizedAnnotation.shape);
            setPaddedLocalBoundingBox(boundingBoxInRoi);
        },
    });

    const handleRoteShape = () => {
        isEditing.current = true;
        const rotatedShape = {
            ...localShape,
            points: rotatePointsAroundPivot(localShape.points, poseLocations.middle, angle),
        };

        setAngle(0);
        setLocalShape(rotatedShape);
        handleComplete(rotatedShape);
        setPaddedLocalBoundingBox(getOuterPaddedBoundingBox(getBoundingBox(rotatedShape), zoomState.zoom));
    };

    return (
        <ClosestKeypoint
            id={`translate-keypoint-${annotation.id}`}
            aria-label={'edit-keypoint'}
            nodes={localShape.points}
            width={image.width}
            height={image.height}
        >
            {(closestPoint) => (
                <g
                    style={{ pointerEvents: 'auto' }}
                    aria-label='rotation group'
                    transform={`rotate(${angle}, ${poseLocations.middle.x}, ${poseLocations.middle.y})`}
                >
                    <RotationAnchor
                        size={14}
                        zoom={zoomState.zoom}
                        pivot={poseLocations.middle}
                        position={{ x: poseLocations.middle.x, y: poseLocations.topWithGap.y }}
                        basePosition={{ x: poseLocations.middle.x, y: poseLocations.top.y }}
                        onComplete={handleRoteShape}
                        onMoveAnchorTo={setAngle}
                    />

                    <TranslateShape
                        disabled={false}
                        zoom={zoomState.zoom}
                        annotation={{ ...annotation, shape: localShape }}
                        onComplete={handleComplete}
                        translateShape={handleTranslate}
                    >
                        <PoseEdges className={classes.layer} shape={localShape} boundingBox={paddedLocalBoundingBox} />
                    </TranslateShape>

                    {localShape.points.map((point, idx) => {
                        return (
                            <EditPosePoint
                                key={`edit-keypoint-${point.label.id}`}
                                roi={roi}
                                point={point}
                                isSelected={isSelected(point.label.id)}
                                isLabelVisible={closestPoint?.label.id === point.label.id}
                                onStart={() => {
                                    setSelected([point.label.id]);
                                }}
                                onToggleVisibility={() => {
                                    handleComplete({ ...localShape, points: toggleVisibility(localShape.points, idx) });
                                }}
                                onComplete={(isUpdated) => {
                                    handleComplete({ ...localShape, points: localShape.points });
                                    isUpdated ? setSelected([point.label.id]) : removeSelected(point.label.id);
                                }}
                                moveAnchorTo={handleMovePointByIndex(idx)}
                            />
                        );
                    })}

                    {boundingBoxResizePoints.map(({ moveAnchorTo, cursor, label, x, y }) => {
                        return (
                            <ResizeAnchor
                                key={label}
                                x={x}
                                y={y}
                                fill={'black'}
                                stroke={'white'}
                                strokeWidth={2}
                                zoom={zoomState.zoom}
                                label={label}
                                cursor={cursor}
                                onComplete={handleComplete}
                                moveAnchorTo={moveAnchorTo}
                            />
                        );
                    })}
                </g>
            )}
        </ClosestKeypoint>
    );
};
