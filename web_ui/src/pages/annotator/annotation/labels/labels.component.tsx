// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { AnimatePresence } from 'framer-motion';
import { isEmpty } from 'lodash-es';
import { useHover } from 'react-aria';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { highestCorner } from '../../../../core/annotations/math';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { isRect } from '../../../../core/annotations/utils';
import { AnnotationToolContext, ToolType } from '../../core/annotation-tool-context.interface';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { AnnotationActions } from './annotation-actions.component';
import { EditLabels } from './edit-labels.component';
import { Label } from './label.component';
import { LabelFlag } from './LabelFlag.component';
import { useLabelPosition } from './use-label-position.hook';
import { getLabelsFromTask, LABEL_CLASS } from './utils';

import classes from './labels.module.scss';

export interface LabelsProps {
    isOverlap?: boolean;
    showOptions?: boolean;
    annotation: Annotation;
    areLabelsInteractive?: boolean;
    annotationToolContext: AnnotationToolContext;
    canEditAnnotationLabel?: boolean;
}

// This value is taken somewhat arbitrarily, it determines the max width the labels of an annotations
// is allowed to take, but it is not precise.
// If the label is a prediction label, then the prediction icon and the confidence percentage add
// a bit of extra space that is not included in this max width.
const MAX_WIDTH_OF_LABELS = 600;

const LABEL_HEIGHT = 24;
const LABEL_OFFSET = 8;
const OUTSIDE_LIMIT = -2;
const KEYPOINT_LABEL_OFFSET = 3;
const ZOOMED_LABEL_HEIGHT = `${LABEL_HEIGHT}px / var(--zoom-level`;

const getTop = (annotation: Annotation, isOverlap = false): number => {
    const offset = isOverlap || isRect(annotation.shape) ? 0 : LABEL_OFFSET;
    const shape = annotation.shape;

    switch (shape.shapeType) {
        case ShapeType.Rect:
            return shape.y;
        case ShapeType.RotatedRect:
            return highestCorner(shape).y - offset;
        case ShapeType.Circle:
            const circleTop = shape.y - shape.r - offset;
            return circleTop > OUTSIDE_LIMIT ? circleTop : OUTSIDE_LIMIT;
        case ShapeType.Polygon:
            const polygonTop = Math.min(...shape.points.map((point) => point.y)) - offset;
            return polygonTop > OUTSIDE_LIMIT ? polygonTop : OUTSIDE_LIMIT;
        case ShapeType.Pose:
            return Math.min(...shape.points.map((point) => point.y)) - KEYPOINT_LABEL_OFFSET;
    }
};

export const Labels = ({
    annotation,
    isOverlap = false,
    showOptions = true,
    annotationToolContext,
    areLabelsInteractive = true,
    canEditAnnotationLabel = true,
}: LabelsProps): JSX.Element => {
    const { selectedTask } = useTask();
    const { x: left, y, height } = useLabelPosition(annotation);

    const [editLabels, setEditLabels] = useState(false);
    const { hoverProps, isHovered } = useHover({ isDisabled: editLabels || !canEditAnnotationLabel });

    const top = isOverlap ? getTop(annotation, isOverlap) + height : getTop(annotation);

    const getZIndex = () => {
        if (!areLabelsInteractive) {
            return undefined;
        }

        if (!annotation.isSelected && annotationToolContext.tool === ToolType.SelectTool) {
            return isHovered ? 2 : 1;
        }
        return undefined;
    };

    const style = {
        left,
        top: isOverlap ? `calc(${top}px + ${ZOOMED_LABEL_HEIGHT})` : top,
        height: `${LABEL_HEIGHT}px`,
        cursor: showOptions ? 'pointer' : 'auto',
        pointerEvents: areLabelsInteractive ? 'auto' : 'none',
        // We allow the user to change labels without explicitly editing an annotation,
        // when they've selected the selection tool.
        // By increasing its zIndex the Labels are rendered on top of the selection tool
        zIndex: getZIndex(),
    } as const;

    if (editLabels) {
        return (
            <>
                <LabelFlag annotation={annotation} top={top} left={left} y={y} />
                <div
                    id={`${annotation.id}-labels`}
                    className={LABEL_CLASS[annotation.shape.shapeType]}
                    // Make sure the label search component overlaps labels from other annotations
                    style={{ ...style, zIndex: 2 }}
                >
                    <EditLabels
                        annotation={annotation}
                        setEditLabels={setEditLabels}
                        annotationToolContext={annotationToolContext}
                    />
                </div>
            </>
        );
    }

    const handleEditLabels = () => {
        showOptions && canEditAnnotationLabel && setEditLabels(true);
    };

    const annotationTaskLabels = getLabelsFromTask(annotation, selectedTask);
    const labels = selectedTask === null ? annotation.labels : annotationTaskLabels;
    const showSelectLabel = isEmpty(labels);

    return (
        <>
            <LabelFlag annotation={annotation} y={y} top={top} left={left} />

            <ul
                id={`${annotation.id}-labels`}
                style={style}
                aria-label={'labels'}
                className={LABEL_CLASS[annotation.shape.shapeType]}
                {...hoverProps}
            >
                {labels.map((label, idx) => {
                    const hasChildren = labels.some(({ parentLabelId }) => label.id === parentLabelId);

                    return (
                        <Label
                            key={label.id}
                            id={`${annotation.id}-labels-${label.id}`}
                            label={label}
                            slots={labels.length}
                            hasChildren={hasChildren}
                            maxWidth={MAX_WIDTH_OF_LABELS}
                            handleEditLabels={canEditAnnotationLabel ? handleEditLabels : undefined}
                            // Make each label overlap its child labels
                            zIndex={labels.length - idx}
                        />
                    );
                })}

                {showOptions && showSelectLabel && (
                    <li className={[classes.label, classes.selectLabel].join(' ')} onClick={handleEditLabels}>
                        Select label
                    </li>
                )}

                <AnimatePresence>
                    {showOptions && isHovered && (
                        <AnnotationActions
                            setEditLabels={setEditLabels}
                            annotation={annotation}
                            annotationToolContext={annotationToolContext}
                        />
                    )}
                </AnimatePresence>
            </ul>
        </>
    );
};
