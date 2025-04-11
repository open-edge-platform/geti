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

import { useEffect, useState } from 'react';

import { Annotation, RegionOfInterest } from '../../../../../core/annotations/annotation.interface';
import { Point } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { sub, Vec2 } from '../../../../../core/annotations/vec2';
import { Labels } from '../../../annotation/labels/labels.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { getMaxCircleRadius, MIN_RADIUS } from '../../circle-tool/utils';
import { isShapeWithinRoi } from '../../utils';
import { ANCHOR_SIZE, ResizeAnchor } from '../resize-anchor.component';
import { ResizeAnchorType } from '../resize-anchor.enum';
import { TranslateShape } from '../translate-shape.component';

import classes from './../../../annotator-canvas.module.scss';

const STROKE_WIDTH = 2;
type Circle = { x: number; y: number; r: number };

interface EditCircleProps {
    annotationToolContext: AnnotationToolContext;
    annotation: Annotation & { shape: { shapeType: ShapeType.Circle } };
    disableTranslation?: boolean;
    disablePoints?: boolean;
}

export const calculateAnchorPoint = ({ x, y }: Vec2, angle: number, radius: number): Vec2 => {
    return {
        x: x - Math.cos(angle) * radius,
        y: y - Math.sin(angle) * radius,
    };
};

const getPreferredAnchorPosition = (circle: Circle, roi: RegionOfInterest, oldAngle?: number): number => {
    const { x, y } = sub(circle, roi);

    // Get position of current angle, or default (right)
    const anchorPosition = calculateAnchorPoint({ x, y }, oldAngle ?? Math.PI, circle.r);

    // Check if the anchor is within the ROI
    if (anchorPosition.x < roi.width && anchorPosition.y > 0 && anchorPosition.y < roi.height) {
        return oldAngle ?? Math.PI;
    }

    // Calculate angle from circle to center of image
    const centerOfROI = { x: roi.width / 2, y: roi.height / 2 };
    const distance = sub({ x, y }, centerOfROI);
    const newAngle = Math.atan(distance.y / distance.x);
    if (distance.x < 0) {
        return newAngle - Math.PI;
    }

    // The circle is drawn in the center of the image, in this case we point
    // the anchor into the top left corner
    if (isNaN(newAngle)) {
        return Math.PI / 4;
    }
    return newAngle;
};

export const EditCircle = ({
    annotationToolContext,
    annotation,
    disablePoints = false,
    disableTranslation = false,
}: EditCircleProps): JSX.Element => {
    const { scene } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();
    const { roi, image } = useROI();
    const [shape, setShape] = useState(annotation.shape);
    const [angle, setAngle] = useState(() => getPreferredAnchorPosition(shape, roi));
    const maxCircleRadius = getMaxCircleRadius(roi);

    useEffect(() => setShape(annotation.shape), [annotation.shape]);

    const onComplete = () => {
        setAngle(getPreferredAnchorPosition(shape, roi, angle));
        updateOrRemoveAnnotation();
    };

    const setConstrainedCircle = ({ x, y, r }: Circle) => {
        setShape({ ...shape, x, y, r: r < MIN_RADIUS ? MIN_RADIUS : r > maxCircleRadius ? maxCircleRadius : r });
    };

    const translate = (inTranslate: Point) => {
        setAngle(getPreferredAnchorPosition(shape, roi));
        setShape({ ...shape, x: shape.x + inTranslate.x, y: shape.y + inTranslate.y });
    };

    const updateOrRemoveAnnotation = () => {
        if (isShapeWithinRoi(roi, shape)) {
            scene.updateAnnotation({ ...annotation, shape });
        } else {
            scene.removeAnnotations([annotation]);
        }
    };

    const anchorPoint = calculateAnchorPoint(shape, angle, shape.r);

    return (
        <>
            <svg
                id={`translate-circle-${annotation.id}`}
                className={classes.disabledLayer}
                width={image.width}
                height={image.height}
            >
                <TranslateShape
                    disabled={disableTranslation}
                    zoom={zoom}
                    annotation={{ ...annotation, shape }}
                    translateShape={translate}
                    onComplete={onComplete}
                />

                <line
                    x1={shape.x}
                    y1={shape.y}
                    x2={anchorPoint.x}
                    y2={anchorPoint.y}
                    stroke='var(--intel-blue)'
                    strokeWidth={STROKE_WIDTH / zoom}
                    strokeDasharray={ANCHOR_SIZE / zoom}
                />
            </svg>

            <Labels annotation={{ ...annotation, shape }} annotationToolContext={annotationToolContext} />

            {disablePoints === false ? (
                <svg
                    id={`edit-circle-points-${annotation.id}`}
                    className={classes.disabledLayer}
                    width={image.width}
                    height={image.height}
                >
                    <g style={{ pointerEvents: 'auto' }}>
                        <ResizeAnchor
                            zoom={zoom}
                            x={anchorPoint.x}
                            y={anchorPoint.y}
                            label='Resize circle anchor'
                            onComplete={onComplete}
                            moveAnchorTo={(x: number, y: number) => {
                                setConstrainedCircle({
                                    x: shape.x,
                                    y: shape.y,
                                    r: Math.round(Math.sqrt(Math.pow(shape.x - x, 2) + Math.pow(shape.y - y, 2))),
                                });
                                setAngle(Math.atan2(shape.y - y, shape.x - x));
                            }}
                            type={ResizeAnchorType.CIRCLE}
                        />
                    </g>
                </svg>
            ) : (
                <></>
            )}
        </>
    );
};
