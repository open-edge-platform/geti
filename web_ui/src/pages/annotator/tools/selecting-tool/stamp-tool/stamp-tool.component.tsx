// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, useRef, useState } from 'react';

import { Annotation as AnnotationInterface } from '../../../../../core/annotations/annotation.interface';
import { isRightButton } from '../../../../buttons-utils';
import { getRelativePoint } from '../../../../utils';
import { Annotation } from '../../../annotation/annotation.component';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { createAnnotation } from '../../../utils';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { SvgToolCanvas } from '../../svg-tool-canvas.component';
import { ToolAnnotationContextProps } from '../../tools.interface';
import { isPointWithinRoi, removeOffLimitPoints, translateAnnotation } from '../../utils';
import { useSelectingState } from '../selecting-state-provider.component';

// NOTE: We allow stamping only one annotation. Below implementation supports also multiple annotations (that's why
// there is array of the annotations), but we don't handle all edge cases for it. In the future we will have to change
// the logic of pasting and the rest should work out of the box.

export const StampTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { stampAnnotations, centerOfTheStampAnnotations } = useSelectingState();
    const { scene } = annotationToolContext;
    const stampToolContainerRef = useRef<SVGRectElement>(null);
    const [translatedAnnotations, setTranslatedAnnotations] = useState<AnnotationInterface[]>(stampAnnotations);
    const { roi, image } = useROI();

    const {
        zoomState: { zoom },
    } = useZoom();

    const handleOnPointerMove = (event: PointerEvent<SVGSVGElement>): void => {
        if (stampToolContainerRef.current === null) {
            return;
        }

        const { clientX, clientY } = event;

        const { x, y } = centerOfTheStampAnnotations;

        const relativeCursorPosition = getRelativePoint(
            stampToolContainerRef.current,
            { x: clientX, y: clientY },
            zoom
        );

        if (!isPointWithinRoi(roi, relativeCursorPosition)) {
            return;
        }

        const translateVector = { x: relativeCursorPosition.x - x, y: relativeCursorPosition.y - y };

        setTranslatedAnnotations(
            stampAnnotations.map((annotation) => translateAnnotation(annotation, translateVector))
        );
    };

    const handleOnPointerDown = (event: PointerEvent<SVGSVGElement>): void => {
        if (stampToolContainerRef.current === null || isRightButton({ button: event.button, buttons: event.buttons })) {
            return;
        }

        const { clientX, clientY } = event;

        const relativeCursorPosition = getRelativePoint(
            stampToolContainerRef.current,
            { x: clientX, y: clientY },
            zoom
        );

        if (!isPointWithinRoi(roi, relativeCursorPosition)) {
            return;
        }

        const newAnnotations = translatedAnnotations.map((annotation) => {
            const { shape, labels } = annotation;

            // NOTE: We could reuse removeOffLimitPoints for rect shapes, but then we would have issues with shape types
            // e.g. in the detection when we check if we get an annotation with proper shape. Therefore, we added custom
            // removeOffPointsRect for rectangles.
            const newShape = removeOffLimitPoints(shape, roi);

            return {
                ...createAnnotation(newShape, labels),
                isSelected: true,
            };
        });

        scene.addAnnotations(newAnnotations);
    };

    return (
        <>
            <SvgToolCanvas
                image={image}
                onPointerDown={handleOnPointerDown}
                onPointerMove={handleOnPointerMove}
                canvasRef={stampToolContainerRef}
                aria-label={'Stamp tool'}
            >
                {translatedAnnotations.map((annotation) => (
                    <Annotation key={annotation.id} annotation={annotation} />
                ))}
            </SvgToolCanvas>
        </>
    );
};
