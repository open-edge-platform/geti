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

import { RefObject, useCallback, useMemo, useRef, useState } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { clampPointBetweenImage } from '../../../../core/annotations/math';
import { isNotKeypointTask } from '../../../../core/projects/utils';
import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { hasEqualId } from '../../../../shared/utils';
import { isRightButton } from '../../../buttons-utils';
import { getRelativePoint } from '../../../utils';
import { useVisibleAnnotations } from '../../hooks/use-visible-annotations.hook';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { getGlobalAnnotations } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { PointerEvents, ToolAnnotationContextProps } from '../tools.interface';
import { SelectingBoxTool } from './components/selecting-box-tool.component';
import { areAnnotationsIdentical, pointInShape } from './utils';

const useClickWithoutDragging = (ref: RefObject<SVGSVGElement>, onClick: (event: PointerEvent) => void) => {
    const [isDragging, setIsDragging] = useState(false);
    const handleClick = useCallback(
        (event: PointerEvent): void => {
            event.preventDefault();

            if (isDragging) {
                return;
            }

            onClick(event);
        },
        [onClick, isDragging]
    );

    useEventListener(PointerEvents.PointerUp, handleClick, ref);
    useEventListener(PointerEvents.PointerDown, () => setIsDragging(false), ref);
    useEventListener(PointerEvents.PointerMove, () => setIsDragging(true), ref);
};

export const SelectingTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { selectedTask, tasks } = useTask();
    const {
        scene: { setSelectedAnnotations },
    } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();

    const selectingContainerRef = useRef<SVGSVGElement>(null);

    const visibleAnnotations = useVisibleAnnotations();
    const { roi, image } = useROI();

    const selectableAnnotations = useMemo(() => {
        const globalAnnotations = getGlobalAnnotations(visibleAnnotations, roi, selectedTask);

        return visibleAnnotations.filter(
            (annotation: Annotation) => !globalAnnotations.some(hasEqualId(annotation.id))
        );
    }, [visibleAnnotations, roi, selectedTask]);

    const handleClick = useCallback(
        (event: PointerEvent): void => {
            event.preventDefault();

            if (
                isRightButton({ button: event.button, buttons: event.buttons }) ||
                selectingContainerRef.current === null
            ) {
                return;
            }

            const clickPoint = { x: event.clientX, y: event.clientY };
            const calculatePoint = getRelativePoint(selectingContainerRef.current, clickPoint, zoom);
            const points = clampPointBetweenImage(image)(calculatePoint);

            const highlightedAnnotations = pointInShape(selectableAnnotations, points, event.shiftKey);
            const identicalAnnotations = areAnnotationsIdentical(selectableAnnotations, highlightedAnnotations);

            if (!identicalAnnotations) {
                setSelectedAnnotations((annotation) => {
                    const isSelected = highlightedAnnotations.find(hasEqualId(annotation.id));

                    if (isSelected) {
                        return isSelected.isSelected;
                    }

                    return annotation.isSelected;
                });
            }
        },
        [zoom, selectableAnnotations, image, setSelectedAnnotations]
    );

    useClickWithoutDragging(selectingContainerRef, handleClick);

    return (
        <svg ref={selectingContainerRef}>
            <SelectingBoxTool
                showLabels={tasks.every(isNotKeypointTask)}
                annotationToolContext={annotationToolContext}
                selectableAnnotations={selectableAnnotations}
            />
        </svg>
    );
};
