// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// the source code ("Material") are owned by Intel Corporation or its suppliers
// or licensors. Title to the Material remains with Intel Corporation or its
// suppliers and licensors. The Material contains trade secrets and proprietary
// and confidential information of Intel or its suppliers and licensors. The
// Material is protected by worldwide copyright and trade secret laws and `treaty
// provisions. No part of the Material may be used, copied, reproduced, modified,
// published, uploaded, posted, transmitted, distributed, or disclosed in any way
// without Intel's prior express written permission.
//
// No license under any patent, copyright, trade secret or other intellectual
// property right is granted to or conferred upon you by disclosure or delivery
// of the Materials, either expressly, by implication, inducement, estoppel or
// otherwise. Any license under such intellectual property rights must be express
// and approved by Intel in writing.

import { intersectionBy } from 'lodash-es';

import { Annotation, AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { roiFromImage } from '../../../../core/annotations/math';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { isCircle, isPolygon } from '../../../../core/annotations/utils';
import { Label } from '../../../../core/labels/label.interface';
import { isExclusive } from '../../../../core/labels/utils';
import { isAnomalyDomain, isClassificationDomain, isDetectionDomain } from '../../../../core/projects/domains';
import { Task } from '../../../../core/projects/task.interface';
import { hasEqualId } from '../../../../shared/utils';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { getGlobalAnnotations } from '../../providers/task-chain-provider/utils';

import classes from './labels.module.scss';

export const LABEL_CLASS: Record<ShapeType, string> = {
    [ShapeType.Rect]: classes.boundingBoxLabel,
    [ShapeType.RotatedRect]: classes.boundingBoxLabel,
    [ShapeType.Circle]: classes.circleLabel,
    [ShapeType.Polygon]: classes.polygonLabel,
    [ShapeType.Pose]: classes.polygonLabel,
};

const getAvailableLabels = (tasks: Task[], selectedTask: Task | null): ReadonlyArray<Label> => {
    return selectedTask === null ? tasks.flatMap((task) => task.labels) : selectedTask.labels;
};

// Get the available labels for the current selected task and the given shape type
export const getAvailableLabelsWithoutEmpty = (tasks: Task[], selectedTask: Task | null): ReadonlyArray<Label> => {
    const labels = getAvailableLabels(tasks, selectedTask);

    return labels.filter((label) => {
        return !isExclusive(label) || label.parentLabelId !== null;
    });
};

export const getAvailableLabelsForAnnotation = (
    annotationToolContext: AnnotationToolContext,
    annotation: Annotation,
    tasks: Task[],
    selectedTask: Task | null,
    image: ImageData
): ReadonlyArray<Label> => {
    const labels = getAvailableLabels(tasks, selectedTask);

    const roi = roiFromImage(image);

    const globalAnnotations = getGlobalAnnotations(annotationToolContext.scene.annotations, roi, selectedTask);
    const isGlobalAnnotation = globalAnnotations.some(hasEqualId(annotation?.id));

    return labels.filter((label) => {
        if (isCircle(annotation?.shape) || isPolygon(annotation?.shape)) {
            const isDetectionLabel = tasks.some(
                (task) => isDetectionDomain(task.domain) && task.labels.some(hasEqualId(label.id))
            );

            if (isDetectionLabel) {
                return false;
            }
        }

        if (selectedTask !== null && isGlobalAnnotation) {
            if (isClassificationDomain(selectedTask.domain) || isAnomalyDomain(selectedTask.domain)) {
                return true;
            }
        }

        return !isExclusive(label) || label.parentLabelId !== null;
    });
};

export const getLabelsFromTask = (annotation: Annotation, task: Task | null): ReadonlyArray<AnnotationLabel> => {
    if (!task) {
        return [];
    }

    return intersectionBy(annotation.labels, task.labels, 'id');
};

export const getLabelsColor = (labels: readonly AnnotationLabel[], selectedTask: Task | null): string | undefined => {
    const taskLabels = selectedTask ? labels.filter((label) => selectedTask.labels.some(hasEqualId(label.id))) : labels;

    return taskLabels.length > 0 ? taskLabels[taskLabels.length - 1].color : undefined;
};
