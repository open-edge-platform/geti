// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { memo } from 'react';

import { Annotation as AnnotationInterface } from '../../../core/annotations/annotation.interface';
import { isLocal, isPrediction } from '../../../core/labels/utils';
import { Task } from '../../../core/projects/task.interface';
import { useIsHovered } from '../../../providers/hovered-provider/hovered-provider.component';
import { DEFAULT_ANNOTATION_STYLES as defaultStyles, EDIT_ANNOTATION_STYLES as editStyles } from '../tools/utils';
import { getLabelsColor } from './labels/utils';
import { ShapeFactory } from './shapes/factory.component';
import { SvgStripedBackgroundPattern } from './svg-striped-background-pattern.component';

interface AnnotationProps {
    annotation: AnnotationInterface;
    isOverlap?: boolean;
    selectedTask?: Task | null;
    isPredictionMode?: boolean;
    maskId?: string;
}

export const Annotation = memo(
    ({
        maskId,
        annotation,
        isPredictionMode = false,
        selectedTask = null,
        isOverlap = false,
    }: AnnotationProps): JSX.Element => {
        const isHovered = useIsHovered(annotation.id);
        const { isSelected, id, labels } = annotation;

        const isEdit = isSelected || isHovered;
        const shapeStyles = !isOverlap && isEdit ? editStyles : {};
        const color = getLabelsColor(labels, selectedTask);

        // If the annotation contains a local prediction label, then we visualize it with a
        // striped background
        const localPredictionLabel = labels.find((label) => isLocal(label) && isPrediction(label));
        const localColor = localPredictionLabel && getLabelsColor([localPredictionLabel], selectedTask);
        const idSvgPattern = `${annotation.id}-pattern`;
        const fill = localPredictionLabel && localColor ? `url(#${idSvgPattern}) ${localColor}` : color;

        return (
            <>
                <g
                    mask={maskId}
                    id={`canvas-annotation-${id}`}
                    {...defaultStyles}
                    strokeLinecap={'round'}
                    strokeDashoffset={'0'}
                    strokeDasharray={isPredictionMode ? '10 6' : '0'}
                    {...(color !== undefined
                        ? {
                              fill,
                              stroke: color,
                              strokeOpacity: 'var(--annotation-border-opacity)',
                          }
                        : {})}
                    {...shapeStyles}
                >
                    <ShapeFactory annotation={annotation} />
                </g>
                {localPredictionLabel && localColor && (
                    <SvgStripedBackgroundPattern annotation={annotation} id={idSvgPattern} color={localColor} />
                )}
            </>
        );
    }
);
