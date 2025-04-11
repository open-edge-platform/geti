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

import intersectionBy from 'lodash/intersectionBy';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import isNil from 'lodash/isNil';

import { Annotation, TaskChainInput } from '../../../../core/annotations/annotation.interface';
import { BoundingBox, getBoundingBox, hasEqualBoundingBox } from '../../../../core/annotations/math';
import { Rect, Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { isRect } from '../../../../core/annotations/utils';
import { Label, LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { isAnomalous, isExclusive, isGlobal, isLocal } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import {
    isAnomalyDomain,
    isClassificationDomain,
    isDetectionDomain,
    isSegmentationDomain,
} from '../../../../core/projects/domains';
import { Task } from '../../../../core/projects/task.interface';
import { hasEqualId } from '../../../../shared/utils';
import { isInsideBoundingBox } from '../../tools/utils';
import { hasValidLabels } from '../../utils';
import { TaskChainContextProps } from './task-chain.interface';

const groupByMany = <T>(list: T[], getKey: (item: T) => string[]) => {
    return list.reduce(
        (previous, currentItem) => {
            const groups = getKey(currentItem);
            groups.forEach((group) => {
                if (!previous[group]) {
                    previous[group] = [];
                }

                previous[group].push(currentItem);
            });

            return previous;
        },
        {} as Record<string, T[]>
    );
};

// Groups annotations into input and output annotations for a selected task.
// The logic for determining wether an annotation is an input is based on its
// labels, while an annotation being an input's output is based on its shape:
// if the center of an annotation's shape lies inside of an input, it is considered
// to be its output.
export const getInputsOutputs = (
    annotations: readonly Annotation[],
    tasks: Task[],
    selectedTask: Task | null
): TaskChainContextProps => {
    const inputs = getInputForTask(annotations, tasks, selectedTask);

    const outputs = selectedTask === null ? annotations : annotations.filter(getFilterAnnotationByTask(selectedTask));

    const inputsWithBoundingBoxes = inputs.map((annotation) => {
        return { ...annotation, boundingBox: getBoundingBox(annotation.shape) };
    });

    // NOTE: for now we group each output into exactly 1 input (possibly the "empty input")
    // later we might want to group it into multiple inputs, but this would require some
    // changes to the useTaskChainOutput hook.
    const grouped = groupByMany(outputs as Annotation[], (output) => {
        // Find all input annotations that containing this output
        const inputsContainingOutput = inputsWithBoundingBoxes.filter(({ boundingBox }) =>
            isInsideBoundingBox(output)(boundingBox)
        );

        // Special case for the first task in a task chain,
        // we implicitely group the outputs into a global annotation
        if (inputsContainingOutput.length === 0) {
            return ['-'];
        }

        return inputsContainingOutput.map(({ id }) => id);
    });

    const inputsWithOutputs = inputs.map((annotation) => {
        // For classification (more specificly global tasks) the input and output annotations are the same
        if (selectedTask !== null && isClassificationDomain(selectedTask.domain)) {
            const containsOutputLabel = ({ labels }: Annotation) => {
                // NOTE for classification this is only false if the input does not contain classification labels
                // this can probably be simplified
                return labels.some(({ id }) => selectedTask?.labels.some(hasEqualId(id)));
            };
            return { ...annotation, outputs: containsOutputLabel(annotation) ? [annotation] : [] };
        }

        const annotationOutputs = grouped[annotation.id] ?? [];

        return { ...annotation, outputs: annotationOutputs };
    });

    return {
        inputs: inputsWithOutputs,
        outputs,
    };
};

export const getPreviousTask = (tasks: Task[], selectedTask: Task | null): Task | null => {
    if (selectedTask === null || tasks.length === 1) {
        return null;
    }

    const idx = tasks.findIndex(hasEqualId(selectedTask?.id));

    return idx - 1 >= 0 ? tasks[idx - 1] : null;
};

const getAnnotationsInsideParentAnnotations = (
    parentAnnotations: ReadonlyArray<Annotation>,
    annotations: Annotation[]
): Annotation[] => {
    const previousBoundingBoxes = parentAnnotations.map(({ shape }) => getBoundingBox(shape));

    return annotations.filter((annotation) => {
        // Don't include annotations that are considered as inputs from the previous task
        if (parentAnnotations.some(hasEqualId(annotation.id))) {
            return false;
        }

        return previousBoundingBoxes.some(isInsideBoundingBox(annotation));
    });
};

export const getFilterAnnotationByTask = (task: Task) => {
    return (annotation: Annotation): boolean => {
        if (isDetectionDomain(task.domain) && !isRect(annotation.shape)) {
            return false;
        }

        return isEmpty(annotation.labels) || annotation.labels.some((label) => task.labels.some(hasEqualId(label.id)));
    };
};

export const getOutputFromTask = (
    annotations: readonly Annotation[],
    tasks: Task[],
    selectedTask: Task | null
): ReadonlyArray<Annotation> => {
    // Don't filter out annotations for single, "All tasks" and Local -> Global tasks
    if (tasks.length === 1 || selectedTask === null) {
        return annotations;
    }

    // In a Local -> Global task the local inputs become the outputs as well
    if (isClassificationDomain(selectedTask.domain)) {
        return getInputForTask(annotations, tasks, selectedTask);
    }

    // In a Local -> Local task, only return annotations that are inside of annotations from a previous task
    if (isSegmentationDomain(selectedTask.domain) || isDetectionDomain(selectedTask.domain)) {
        const filteredAnnotations = annotations.filter(getFilterAnnotationByTask(selectedTask));

        const previousTask = getPreviousTask(tasks, selectedTask);

        if (isNil(previousTask)) {
            return filteredAnnotations;
        }

        const selectedInputs = getInputForTask(annotations, tasks, selectedTask).filter(({ isSelected }) => isSelected);

        return getAnnotationsInsideParentAnnotations(selectedInputs, filteredAnnotations);
    }

    return [];
};

const annotationContainsEmptyLabel = (annotation: Annotation, task: Task): boolean => {
    return annotation.labels.some((label) => isExclusive(label) && task.labels.some(hasEqualId(label.id)));
};

export const getGlobalAnnotations = (
    annotations: ReadonlyArray<Annotation>,
    roi: BoundingBox,
    selectedTask: Task | null
) => {
    const globalAnnotations = annotations.filter((annotation) => {
        if (!isRect(annotation.shape)) {
            return false;
        }

        if (
            selectedTask === null ||
            (!isClassificationDomain(selectedTask.domain) && !isAnomalyDomain(selectedTask.domain))
        ) {
            // In case of a detection or segmentation project we want to show
            // the annotation's shape if it does not yet have a global label
            if (!annotation.labels.some(isGlobal)) {
                return false;
            }
        }

        // In "all tasks" mode the only "global" annotation can be one that has no local annotations,
        if (selectedTask === null && annotation.labels.some(isLocal)) {
            return false;
        }

        return hasEqualBoundingBox(getBoundingBox(annotation.shape), roi);
    });

    // Hacky way to make sure that there is only 1 global annotation,
    // this allows a user to have both a global anomalous annotation in anomaly
    // detection and a local anomalous annotation of the same size
    if (!isEmpty(globalAnnotations)) {
        return [globalAnnotations[0]];
    }

    return [];
};

export const getInputForTask = (
    annotations: readonly Annotation[],
    tasks: Task[],
    selectedTask: Task | null
): ReadonlyArray<Annotation> => {
    const previousTask = getPreviousTask(tasks, selectedTask);

    if (isNil(previousTask)) {
        // NOTE: since classification is a global task its input and output
        // annotations are the same.
        // One caveat is that in Detection -> Classification we will also show
        // detection annotations without labels
        if (selectedTask?.domain === DOMAIN.CLASSIFICATION) {
            return getOutputFromTask(annotations, tasks, selectedTask);
        }

        return [];
    }

    const output = getOutputFromTask(annotations, tasks, previousTask).filter(
        (annotation) => !annotationContainsEmptyLabel(annotation, previousTask)
    );

    if (selectedTask?.domain === DOMAIN.CLASSIFICATION) {
        return output;
    }

    return output.filter(hasValidLabels);
};

interface LabelConflictPredicate {
    (label: Label, otherLabel: Label): boolean;
}

const isLocalLabel = (label: Label) => label.behaviour === LABEL_BEHAVIOUR.LOCAL;

export const getLabelConflictPredicate = (tasks: Task[]): LabelConflictPredicate => {
    return (label: Label, otherLabel: Label) => {
        const hasEqualGroups = label.group === otherLabel.group;
        const areLocalLabels = isLocalLabel(label) && isLocalLabel(otherLabel);

        if (hasEqualGroups || areLocalLabels) {
            return true;
        }

        if (isExclusive(label) || isExclusive(otherLabel)) {
            const task = tasks.find(({ labels }) => labels.some(hasEqualId(label.id)));
            const otherTask = tasks.find(({ labels }) => labels.some(hasEqualId(otherLabel.id)));
            return task?.id === otherTask?.id;
        }

        return false;
    };
};

export const getAnnotationsWithSelectedInput = (
    annotations: ReadonlyArray<Annotation>,
    inputAnnotations: ReadonlyArray<Annotation>
): ReadonlyArray<Annotation> => {
    const visibleInputAnnotations = inputAnnotations.filter(({ isHidden }) => !isHidden);

    const selectedInputAnnotations = visibleInputAnnotations.filter(({ isSelected }) => isSelected);

    if (isEmpty(visibleInputAnnotations) || selectedInputAnnotations.length === 1) {
        return annotations;
    }

    if (isEmpty(selectedInputAnnotations)) {
        // Make sure that at least one of the inputs is selected, defaulting
        // to the last drawn visible input as this is most likely to not be annotated
        // TODO: first check if there is a partially annotated annotation so that this can be selected instead
        const lastAnnotation = visibleInputAnnotations[visibleInputAnnotations.length - 1];

        return annotations.map((annotation) => {
            if (annotation.id === lastAnnotation.id) {
                return { ...annotation, isSelected: true };
            }

            return annotation;
        });
    }

    // Deselect all annotations except the last one
    const lastAnnotation = selectedInputAnnotations[selectedInputAnnotations.length - 1];

    return annotations.map((annotation) => {
        const isSelectedInput = annotation.isSelected && selectedInputAnnotations.some(hasEqualId(annotation.id));

        if (isSelectedInput) {
            return { ...annotation, isSelected: annotation.id === lastAnnotation.id };
        }

        return annotation;
    });
};

export const getSelectedInputAnnotations = (
    annotations: ReadonlyArray<Annotation>,
    inputAnnotations: ReadonlyArray<Annotation>
): ReadonlyArray<Annotation> => {
    return annotations.filter(({ isSelected, id }) => {
        return isSelected && inputAnnotations.some(hasEqualId(id));
    });
};

export const possiblyAddGlobalAnomalousShape = (
    shapes: Shape[],
    labels: Label[] | null,
    existingAnnotations: ReadonlyArray<Annotation>,
    roi: Omit<Rect, 'shapeType'> | undefined
): Shape[] => {
    if (roi === undefined || labels === null || !labels.some(isAnomalous)) {
        return shapes;
    }

    const containsAGlobalShape = shapes.some((shape) => {
        return hasEqualBoundingBox(roi, getBoundingBox(shape));
    });

    if (containsAGlobalShape) {
        return shapes;
    }

    const hasAnomalousGlobalAnnotation = existingAnnotations.some((annotation) => {
        if (isEmpty(intersectionBy(annotation.labels, labels, 'id'))) {
            return false;
        }

        return hasEqualBoundingBox(roi, getBoundingBox(annotation.shape));
    });

    if (hasAnomalousGlobalAnnotation) {
        return shapes;
    }

    // Add an extra global anomalous shape
    const globalAnomalousShape = { shapeType: ShapeType.Rect, ...roi } as const;
    return [globalAnomalousShape, ...shapes];
};

export const getGlobalAnnotationsWithoutLabels = (
    annotations: ReadonlyArray<Annotation>,
    roi: Omit<Rect, 'shapeType'>
) => {
    return annotations.filter((annotation) => {
        if (!isRect(annotation.shape)) {
            return false;
        }

        if (!isEmpty(annotation.labels)) {
            return false;
        }

        return hasEqualBoundingBox(getBoundingBox(annotation.shape), roi);
    });
};

export const containsGlobalAnnotationWithLabel = (
    annotations: ReadonlyArray<Annotation>,
    label: Label,
    imageRoi: Shape | undefined
): boolean => {
    return annotations.some((annotation) => {
        if (!annotation.labels.some(hasEqualId(label.id))) {
            return false;
        }

        return isEqual(annotation.shape, imageRoi);
    });
};

export const getTaskChainOutput = (
    inputs: readonly TaskChainInput[],
    outputs: readonly Annotation[],
    tasks: Task[],
    selectedTask: Task | null
): Annotation[] => {
    const previousTask = getPreviousTask(tasks, selectedTask);

    if (isNil(previousTask)) {
        // There is no associated input to our outputs when we don't have a previous task,
        // so instead we always return all outputs
        return [...outputs];
    }

    const isTaskChainSelectedClassification =
        tasks.length > 1 && !isNil(selectedTask) && isClassificationDomain(selectedTask.domain);
    if (isTaskChainSelectedClassification) {
        // Task chain classification is special in that its outputs are the inputs
        return [...inputs];
    }

    return inputs.filter(({ isSelected }) => isSelected).flatMap((input) => input.outputs);
};

export const getTaskChainInputsOutput =
    (tasks: Task[], selectedTask: Task | null) =>
    (annotations: readonly Annotation[]): [Annotation[], readonly TaskChainInput[]] => {
        const inputForTask = getInputForTask(annotations, tasks, selectedTask);
        const selectedAnnotations = getAnnotationsWithSelectedInput(annotations, inputForTask);

        const { inputs, outputs } = getInputsOutputs(selectedAnnotations, tasks, selectedTask);

        return [getTaskChainOutput(inputs, outputs, tasks, selectedTask), inputs];
    };
