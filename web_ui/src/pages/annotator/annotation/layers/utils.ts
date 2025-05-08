// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { isNil } from 'lodash-es';

import { Annotation as AnnotationInterface } from '../../../../core/annotations/annotation.interface';
import { Explanation } from '../../../../core/annotations/prediction.interface';
import { Task } from '../../../../core/projects/task.interface';
import { hasEqualId } from '../../../../shared/utils';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { filterForExplanation, hasValidLabels } from '../../utils';

interface BaseLayer {
    width: number;
    height: number;
    hideLabels?: boolean;
    annotations: AnnotationInterface[];
    canEditAnnotationLabel?: boolean;
}

export interface LayersProps extends BaseLayer {
    showLabelOptions?: boolean;
    areLabelsInteractive?: boolean;
    annotationToolContext: AnnotationToolContext;
    annotationsFilter: (
        annotations: AnnotationInterface[],
        extraFilter?: (a: AnnotationInterface) => boolean
    ) => AnnotationInterface[];
}

export interface LayerProps extends BaseLayer {
    isOverlap?: boolean;
    selectedTask: Task | null;
    isPredictionMode: boolean;
    removeBackground?: boolean;
    globalAnnotations: AnnotationInterface[];
    renderLabel: (annotation: AnnotationInterface) => ReactNode;
}

export const isExplanationSelected = (
    isExplanationVisible: boolean,
    selectedExplanation: Explanation | undefined
): selectedExplanation is Explanation => isExplanationVisible && !isNil(selectedExplanation);

export const filterByExplanationSelection = (
    annotations: AnnotationInterface[],
    isClassification: boolean,
    selectedExplanation: Explanation
) => {
    return annotations
        .filter(filterForExplanation(selectedExplanation, true))
        .map((annotation) => {
            const labels = isClassification
                ? annotation.labels.filter(hasEqualId(selectedExplanation.labelsId))
                : annotation.labels;

            return { ...annotation, labels };
        })
        .filter(hasValidLabels);
};
