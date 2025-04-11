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

import { ReactNode } from 'react';

import isNil from 'lodash/isNil';

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
