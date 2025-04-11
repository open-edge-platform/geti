// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, Fragment, PointerEvent, RefObject, SetStateAction, useState } from 'react';

import { Annotation as AnnotationInterface } from '../../../../../core/annotations/annotation.interface';
import { clampPointBetweenImage } from '../../../../../core/annotations/math';
import { Point } from '../../../../../core/annotations/shapes.interface';
import { isRightButton } from '../../../../buttons-utils';
import { getRelativePoint } from '../../../../utils';
import { Annotation } from '../../../annotation/annotation.component';
import { Labels } from '../../../annotation/labels/labels.component';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { ToolAnnotationContextProps } from '../../tools.interface';
import { translateAnnotation } from '../../utils';

interface TranslatedAnnotationsProps extends ToolAnnotationContextProps {
    showLabels: boolean;
    translatedAnnotations: AnnotationInterface[] | null;
    setTranslatedAnnotations: Dispatch<SetStateAction<AnnotationInterface[] | null>>;
    canvasRef: RefObject<SVGRectElement | null>;
}

export const TranslatedAnnotations = ({
    canvasRef,
    showLabels,
    translatedAnnotations,
    annotationToolContext,
    setTranslatedAnnotations,
}: TranslatedAnnotationsProps): JSX.Element => {
    const {
        scene: { updateAnnotation },
    } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();

    const { image } = useROI();
    const [startPoint, setStartPoint] = useState<Point | null>(null);

    const clampPoint = clampPointBetweenImage(image);

    const handleShapesBoxPointerDown = (event: PointerEvent<SVGSVGElement>): void => {
        const { button, buttons, clientX, clientY, currentTarget, pointerId } = event;

        if (canvasRef.current === null || isRightButton({ button, buttons }) || translatedAnnotations === null) {
            return;
        }

        const relative = clampPoint(getRelativePoint(canvasRef.current, { x: clientX, y: clientY }, zoom));

        setStartPoint(relative);

        currentTarget.setPointerCapture(pointerId);
    };

    const handleShapesBoxPointerMove = (event: PointerEvent<SVGSVGElement>): void => {
        const { button, buttons, clientY, clientX, currentTarget, pointerId } = event;

        if (
            canvasRef.current === null ||
            isRightButton({ button, buttons }) ||
            !currentTarget.hasPointerCapture(pointerId) ||
            translatedAnnotations === null ||
            startPoint === null
        ) {
            return;
        }

        const relative = clampPoint(getRelativePoint(canvasRef.current, { x: clientX, y: clientY }, zoom));

        const translateVector = {
            x: relative.x - startPoint.x,
            y: relative.y - startPoint.y,
        };

        setStartPoint(relative);

        setTranslatedAnnotations((previousAnnotations) => {
            if (previousAnnotations === null || previousAnnotations.length <= 1) {
                return null;
            }

            const annotations = previousAnnotations.map((annotation) =>
                translateAnnotation(annotation, translateVector)
            );

            return annotations;
        });
    };

    const handleShapesBoxPointerUp = (event: PointerEvent<SVGSVGElement>): void => {
        const { button, buttons, currentTarget, pointerId } = event;
        if (
            canvasRef.current === null ||
            isRightButton({ button, buttons }) ||
            !currentTarget.hasPointerCapture(pointerId) ||
            translatedAnnotations === null
        ) {
            return;
        }

        translatedAnnotations.forEach((annotation) => {
            updateAnnotation(annotation);
        });

        setStartPoint(null);
        currentTarget.releasePointerCapture(pointerId);
    };

    return (
        <>
            {translatedAnnotations?.map((annotation) => (
                <Fragment key={annotation.id}>
                    <svg
                        style={{ cursor: 'move' }}
                        onPointerDown={handleShapesBoxPointerDown}
                        onPointerMove={handleShapesBoxPointerMove}
                        onPointerUp={handleShapesBoxPointerUp}
                    >
                        <Annotation annotation={annotation} />
                    </svg>
                    {showLabels && (
                        <foreignObject style={{ height: '100%', width: '100%', pointerEvents: 'none' }}>
                            <Labels annotation={annotation} annotationToolContext={annotationToolContext} />
                        </foreignObject>
                    )}
                </Fragment>
            ))}
        </>
    );
};
