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

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Point } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { Labels } from '../../../annotation/labels/labels.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { ANCHOR_SIZE, ResizeAnchor } from '../resize-anchor.component';
import { TranslateShape } from '../translate-shape.component';
import { getBoundingBoxInRoi, getBoundingBoxResizePoints, getClampedBoundingBox } from '../utils';

import classes from './../../../annotator-canvas.module.scss';

interface EditBoundingBoxProps {
    annotationToolContext: AnnotationToolContext;
    annotation: Annotation & { shape: { shapeType: ShapeType.Rect } };
    disableTranslation?: boolean;
    disablePoints?: boolean;
}

export const EditBoundingBox = ({
    annotationToolContext,
    annotation,
    disablePoints = false,
    disableTranslation = false,
}: EditBoundingBoxProps): JSX.Element => {
    const [shape, setShape] = useState(annotation.shape);

    useEffect(() => setShape(annotation.shape), [annotation.shape]);

    const { scene } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();
    const { roi, image } = useROI();

    const onComplete = () => {
        scene.updateAnnotation({ ...annotation, shape });
    };

    const translate = (point: Point) => {
        const newBoundingBox = getClampedBoundingBox(point, shape, roi);

        setShape({ ...shape, ...newBoundingBox });
    };

    const anchorPoints = getBoundingBoxResizePoints({
        gap: (2 * ANCHOR_SIZE) / zoom,
        boundingBox: shape,
        onResized: (boundingBox) => {
            setShape({ ...shape, ...getBoundingBoxInRoi(boundingBox, roi) });
        },
    });

    return (
        <>
            <svg
                width={image.width}
                height={image.height}
                className={classes.disabledLayer}
                id={`translate-bounding-box-${annotation.id}`}
            >
                <TranslateShape
                    disabled={disableTranslation}
                    zoom={zoom}
                    annotation={{ ...annotation, shape }}
                    translateShape={translate}
                    onComplete={onComplete}
                />
            </svg>

            <Labels annotation={{ ...annotation, shape }} annotationToolContext={annotationToolContext} />

            {disablePoints === false ? (
                <svg
                    width={image.width}
                    height={image.height}
                    className={classes.disabledLayer}
                    aria-label={`Edit bounding box points ${annotation.id}`}
                    id={`edit-bounding-box-points-${annotation.id}`}
                >
                    <g style={{ pointerEvents: 'auto' }}>
                        {anchorPoints.map((anchor) => {
                            return <ResizeAnchor key={anchor.label} zoom={zoom} onComplete={onComplete} {...anchor} />;
                        })}
                    </g>
                </svg>
            ) : (
                <></>
            )}
        </>
    );
};
