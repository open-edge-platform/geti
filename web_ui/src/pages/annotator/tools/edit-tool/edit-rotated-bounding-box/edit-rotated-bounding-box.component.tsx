// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { clampBetween, rotatedRectCorners } from '../../../../../core/annotations/math';
import {
    calculateSizeAndPositionBasedOfCornerAnchor,
    calculateSizeAndPositionOfSideAnchor,
    cursorForDirection,
} from '../../../../../core/annotations/rotated-rect-math';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import * as Vec2 from '../../../../../core/annotations/vec2';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { isShapeWithinRoi } from '../../utils';
import { ANCHOR_SIZE, ResizeAnchor } from '../resize-anchor.component';
import { ResizeAnchorType } from '../resize-anchor.enum';
import { TranslateShape } from '../translate-shape.component';
import { getSideAnchorLocations } from './location';
import { RotationElement } from './rotation-element/rotation-element.component';

import classes from './../../../annotator-canvas.module.scss';

interface EditRotatedBoundingBoxProps {
    annotationToolContext: AnnotationToolContext;
    annotation: Annotation & { shape: { shapeType: ShapeType.RotatedRect } };
    disableTranslation?: boolean;
    disablePoints?: boolean;
}

export const EditRotatedBoundingBox = ({
    annotationToolContext,
    annotation,
    disablePoints = false,
    disableTranslation = false,
}: EditRotatedBoundingBoxProps): JSX.Element => {
    const [shape, setShape] = useState(annotation.shape);

    useEffect(() => setShape(annotation.shape), [annotation.shape]);

    const { scene } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();
    const { roi, image } = useROI();

    const onComplete = () => {
        if (isShapeWithinRoi(roi, shape)) {
            scene.updateAnnotation({ ...annotation, shape });
        } else {
            scene.removeAnnotations([annotation]);
        }
    };

    const translate = (point: { x: number; y: number }) => {
        const clampedTranslate = {
            x: clampBetween(shape.x - roi.width, -point.x, shape.x),
            y: clampBetween(shape.y - roi.height, -point.y, shape.y),
        };

        setShape({ ...shape, x: shape.x - clampedTranslate.x, y: shape.y - clampedTranslate.y });
    };

    const gap = (2 * ANCHOR_SIZE) / zoom;
    const sideAnchorLocations = getSideAnchorLocations(shape, gap);
    const cornerAnchorLocations = rotatedRectCorners(shape);
    const cornerLabels = ['North west', 'North east', 'South east', 'South west'];
    const cornerAnchors = cornerAnchorLocations.map((corner: Vec2.Vec2, index: number) => {
        const opposite = cornerAnchorLocations[(index + 2) % 4];
        return {
            ...corner,
            moveAnchorTo: (x: number, y: number) => {
                setShape({
                    ...shape,
                    ...calculateSizeAndPositionBasedOfCornerAnchor({ x, y }, corner, opposite, shape, gap),
                });
            },
            cursor: cursorForDirection(corner, opposite),
            label: `${cornerLabels[index]} resize anchor`,
        };
    });

    cursorForDirection(sideAnchorLocations.E, sideAnchorLocations.W);

    const anchorPoints = [
        {
            ...sideAnchorLocations.N,
            moveAnchorTo: (x: number, y: number) => {
                const result = calculateSizeAndPositionOfSideAnchor(
                    { x, y },
                    sideAnchorLocations.N,
                    sideAnchorLocations.S,
                    gap
                );
                setShape({
                    ...shape,
                    x: result.x,
                    y: result.y,
                    height: result.size,
                });
            },
            cursor: cursorForDirection(sideAnchorLocations.N, sideAnchorLocations.S),
            label: `North resize anchor`,
        },
        {
            ...sideAnchorLocations.S,
            moveAnchorTo: (x: number, y: number) => {
                const result = calculateSizeAndPositionOfSideAnchor(
                    { x, y },
                    sideAnchorLocations.S,
                    sideAnchorLocations.N,
                    gap
                );
                setShape({
                    ...shape,
                    x: result.x,
                    y: result.y,
                    height: result.size,
                });
            },
            cursor: cursorForDirection(sideAnchorLocations.S, sideAnchorLocations.N),
            label: `South resize anchor`,
        },
        {
            ...sideAnchorLocations.E,
            moveAnchorTo: (x: number, y: number) => {
                const result = calculateSizeAndPositionOfSideAnchor(
                    { x, y },
                    sideAnchorLocations.E,
                    sideAnchorLocations.W,
                    gap
                );
                setShape({
                    ...shape,
                    x: result.x,
                    y: result.y,
                    width: result.size,
                });
            },
            cursor: cursorForDirection(sideAnchorLocations.E, sideAnchorLocations.W),
            label: `East resize anchor`,
        },
        {
            ...sideAnchorLocations.W,
            moveAnchorTo: (x: number, y: number) => {
                const result = calculateSizeAndPositionOfSideAnchor(
                    { x, y },
                    sideAnchorLocations.W,
                    sideAnchorLocations.E,
                    gap
                );
                setShape({
                    ...shape,
                    x: result.x,
                    y: result.y,
                    width: result.size,
                });
            },
            cursor: cursorForDirection(sideAnchorLocations.W, sideAnchorLocations.E),
            label: `West resize anchor`,
        },
        ...cornerAnchors,
    ];

    return (
        <>
            <svg
                id={`translate-bounding-box-${annotation.id}`}
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
            </svg>

            {disablePoints === false ? (
                <svg
                    id={`edit-bounding-box-points-${annotation.id}`}
                    className={classes.disabledLayer}
                    width={image.width}
                    height={image.height}
                >
                    <g style={{ pointerEvents: 'auto' }}>
                        <RotationElement
                            zoom={zoom}
                            onComplete={onComplete}
                            shape={shape}
                            setShape={setShape}
                            sideAnchorLocations={sideAnchorLocations}
                            roi={roi}
                        />
                        {anchorPoints.map((anchor) => {
                            return (
                                <ResizeAnchor
                                    key={anchor.label}
                                    zoom={zoom}
                                    type={ResizeAnchorType.SQUARE}
                                    onComplete={onComplete}
                                    angle={shape.angle}
                                    {...anchor}
                                />
                            );
                        })}
                    </g>
                </svg>
            ) : (
                <></>
            )}
        </>
    );
};
