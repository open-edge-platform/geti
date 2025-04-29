// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, useEffect, useMemo, useRef, useState } from 'react';

import isEmpty from 'lodash/isEmpty';
import { useHotkeys } from 'react-hotkeys-hook';

import { Annotation, Annotation as AnnotationInterface } from '../../../../../core/annotations/annotation.interface';
import { clampBox, clampPointBetweenImage, isPointInShape, pointsToRect } from '../../../../../core/annotations/math';
import { Point, Rect } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { hasEqualId } from '../../../../../shared/utils';
import { isRightButton } from '../../../../buttons-utils';
import { getRelativePoint } from '../../../../utils';
import { Rectangle } from '../../../annotation/shapes/rectangle.component';
import { useAnnotatorHotkeys } from '../../../hooks/use-hotkeys-configuration.hook';
import { useVisibleAnnotations } from '../../../hooks/use-visible-annotations.hook';
import { HOTKEY_OPTIONS } from '../../../hot-keys/utils';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { SvgToolCanvas } from '../../svg-tool-canvas.component';
import { ToolAnnotationContextProps } from '../../tools.interface';
import { SELECT_ANNOTATION_STYLES } from '../../utils';
import { getIntersectedAnnotationsIds } from '../utils';
import { TranslatedAnnotations } from './translated-annotations.component';

const selectIntersectedAnnotations = (annotations: Annotation[], ids: string[]) => {
    return annotations
        .filter((annotation) => ids.some((id) => id === annotation.id))
        .map((annotation) => ({ ...annotation, isSelected: true }));
};

interface SelectingBoxToolProps extends ToolAnnotationContextProps {
    showLabels: boolean;
    selectableAnnotations: Annotation[];
}
export const SelectingBoxTool = ({
    showLabels,
    annotationToolContext,
    selectableAnnotations,
}: SelectingBoxToolProps): JSX.Element => {
    const { hotkeys } = useAnnotatorHotkeys();
    const {
        scene: { unselectAllAnnotations, setSelectedAnnotations },
    } = annotationToolContext;
    const { roi, image } = useROI();

    const canvasRef = useRef<SVGRectElement | null>(null);
    const [startPoint, setStartPoint] = useState<Point | null>(null);
    const [selectionBox, setSelectionBox] = useState<Rect | null>(null);
    const clampPoint = clampPointBetweenImage(image);
    const [translatedAnnotations, setTranslatedAnnotations] = useState<AnnotationInterface[] | null>(null);
    const visibleAnnotations = useVisibleAnnotations();
    const selectedAnnotations = useMemo(
        () => visibleAnnotations.filter(({ isSelected }) => isSelected),
        [visibleAnnotations]
    );
    const localCopyOfLastSelectedAnnotations = useRef<AnnotationInterface[] | null>(null);

    const {
        zoomState: { zoom },
    } = useZoom();

    const handlePointerDown = (event: PointerEvent<SVGSVGElement>): void => {
        const { button, buttons, clientY, clientX, currentTarget, pointerId, shiftKey } = event;

        if (canvasRef.current === null || isRightButton({ button, buttons })) {
            return;
        }

        const relativePoint = clampPoint(getRelativePoint(canvasRef.current, { x: clientX, y: clientY }, zoom));

        if (
            !shiftKey &&
            translatedAnnotations !== null &&
            translatedAnnotations.some((annotation) => isPointInShape(annotation.shape, relativePoint))
        ) {
            return;
        }

        setStartPoint(relativePoint);

        setSelectionBox({ shapeType: ShapeType.Rect, x: relativePoint.x, y: relativePoint.y, width: 0, height: 0 });

        currentTarget.setPointerCapture(pointerId);
    };

    const checkIfAnnotationShouldBeToggledWithShiftKey = (
        intersectedAnnotations: AnnotationInterface[],
        annotationId: string
    ) => {
        const annotationExists = intersectedAnnotations.find(hasEqualId(annotationId));
        const wasAnnotationsSelectedPreviously = Boolean(
            localCopyOfLastSelectedAnnotations.current?.find(hasEqualId(annotationId))
        );

        return !wasAnnotationsSelectedPreviously && annotationExists !== undefined;
    };

    const handlePointerMoveWithShiftKey = (intersectedAnnotations: AnnotationInterface[]) => {
        const updateState = (prevAnnotations: AnnotationInterface[]) => {
            if (prevAnnotations === null) {
                return intersectedAnnotations;
            }

            const newSelectedAnnotations: AnnotationInterface[] = prevAnnotations.map((annotation) => {
                const shouldAnnotationBeToggled = checkIfAnnotationShouldBeToggledWithShiftKey(
                    intersectedAnnotations,
                    annotation.id
                );

                if (shouldAnnotationBeToggled) {
                    return {
                        ...annotation,
                        isSelected: !annotation.isSelected,
                    };
                }

                return annotation;
            });

            intersectedAnnotations.forEach((annotation) => {
                const hasAnnotation = newSelectedAnnotations.find(hasEqualId(annotation.id));
                if (hasAnnotation) {
                    return;
                }

                newSelectedAnnotations.push(annotation);
            });

            localCopyOfLastSelectedAnnotations.current = intersectedAnnotations;

            return newSelectedAnnotations;
        };

        setTranslatedAnnotations(updateState(translatedAnnotations ?? []));
    };

    const handlePointerMove = (event: PointerEvent<SVGSVGElement>): void => {
        const { button, buttons, clientY, clientX, currentTarget, pointerId, shiftKey: isShiftKeyDown } = event;
        if (
            canvasRef.current === null ||
            isRightButton({ button, buttons }) ||
            !currentTarget.hasPointerCapture(pointerId) ||
            selectionBox === null ||
            startPoint === null
        ) {
            return;
        }

        const relative = clampPoint(getRelativePoint(canvasRef.current, { x: clientX, y: clientY }, zoom));

        const newBox = {
            ...selectionBox,
            ...clampBox(pointsToRect({ x: startPoint.x, y: startPoint.y }, { x: relative.x, y: relative.y }), roi),
        };

        setSelectionBox(newBox);

        const intersectedAnnotationsIds = getIntersectedAnnotationsIds(selectableAnnotations, newBox);

        const intersectedAnnotations = selectIntersectedAnnotations(visibleAnnotations, intersectedAnnotationsIds);

        if (isEmpty(intersectedAnnotations) && !isShiftKeyDown) {
            setTranslatedAnnotations((prevAnnotations) =>
                prevAnnotations ? prevAnnotations.map((annotation) => ({ ...annotation, isSelected: false })) : null
            );
        } else {
            // While multiple selection we use translatedAnnotations as the local annotations. It means that we don't
            // change global (annotations from the scene) until the pointer is up - it reduces amount of rerenders.
            // This component is responsible for drawing selected annotations. Therefore, we need to store all the
            // previously selected annotations even though they are not selected the current pointer move event.

            if (isShiftKeyDown) {
                handlePointerMoveWithShiftKey(intersectedAnnotations);
            } else {
                setTranslatedAnnotations((prevAnnotations) => {
                    if (prevAnnotations === null) {
                        return intersectedAnnotations;
                    }

                    const newAnnotations = prevAnnotations.map((annotation) => {
                        // Check if the intersected annotation is in the previous annotations, if it is we want to that
                        // annotation with selected styles.
                        const annotationExists = intersectedAnnotations.find(hasEqualId(annotation.id));

                        return { ...annotation, isSelected: annotationExists !== undefined };
                    });

                    // Check if the intersected annotations are not part of the previously selected annotations.
                    // If they are not, add them to the array.
                    intersectedAnnotations.forEach((annotation) => {
                        const annotationExists = prevAnnotations.find(hasEqualId(annotation.id));

                        if (annotationExists) {
                            return;
                        }

                        newAnnotations.push(annotation);
                    });

                    return newAnnotations;
                });
            }
        }
    };

    const handlePointerUp = (event: PointerEvent<SVGSVGElement>): void => {
        const { button, buttons, currentTarget, pointerId } = event;

        if (
            canvasRef.current === null ||
            isRightButton({ button, buttons }) ||
            !currentTarget.hasPointerCapture(pointerId) ||
            selectionBox === null ||
            startPoint === null
        ) {
            return;
        }

        if (selectionBox.height > 0 && selectionBox.height > 0 && translatedAnnotations !== null) {
            setSelectedAnnotations((inputAnnotation) => {
                const annotation = translatedAnnotations.find(hasEqualId(inputAnnotation.id));

                if (annotation) {
                    return annotation.isSelected;
                }

                return inputAnnotation.isSelected;
            });
        }

        setStartPoint(null);
        setSelectionBox(null);
        localCopyOfLastSelectedAnnotations.current = null;

        currentTarget.releasePointerCapture(pointerId);
    };

    useHotkeys(
        hotkeys.close,
        () => {
            if (startPoint !== null && selectionBox !== null) {
                setStartPoint(null);
                setSelectionBox(null);
                setTranslatedAnnotations(null);
                unselectAllAnnotations();
            }
        },
        HOTKEY_OPTIONS,
        [startPoint, selectionBox]
    );

    useEffect(() => {
        // NOTE: We do it in reactive approach, because we need to consider shift key to select more annotations.
        // Using that we listen to selectedAnnotations change and whenever it changes we update translated annotations.
        if (selectedAnnotations.length > 1) {
            setTranslatedAnnotations(selectedAnnotations);
            return;
        }

        setTranslatedAnnotations(null);
    }, [selectedAnnotations]);

    return (
        <SvgToolCanvas
            image={image}
            canvasRef={canvasRef}
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
            onPointerMove={handlePointerMove}
        >
            <TranslatedAnnotations
                showLabels={showLabels}
                translatedAnnotations={translatedAnnotations}
                setTranslatedAnnotations={setTranslatedAnnotations}
                canvasRef={canvasRef}
                annotationToolContext={annotationToolContext}
            />
            {selectionBox && (
                <Rectangle shape={selectionBox} styles={{ ...SELECT_ANNOTATION_STYLES, role: 'application' }} />
            )}
        </SvgToolCanvas>
    );
};
