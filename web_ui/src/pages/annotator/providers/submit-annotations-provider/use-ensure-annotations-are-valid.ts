// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { identity, isEqual } from 'lodash-es';
import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Rect } from '../../../../core/annotations/shapes.interface';
import { isRect, labelFromUser } from '../../../../core/annotations/utils';
import { isAnomalous } from '../../../../core/labels/utils';
import { isAnomalyDomain, isClassificationDomain } from '../../../../core/projects/domains';
import { Task } from '../../../../core/projects/task.interface';
import { useImageROI } from '../../hooks/use-image-roi.hook';
import { getLabeledShape, hasValidLabels } from '../../utils';
import { useTask } from '../task-provider/task-provider.component';

// If the user did not classify the media item, then we won't save any annotations
const ensureClassificationAnnotationsAreConsistent = (annotations: ReadonlyArray<Annotation>) =>
    annotations.filter(hasValidLabels);

const isGlobalAnnotation = (annotation: Annotation, imageRoi: Rect) => {
    if (!isRect(annotation.shape)) {
        return false;
    }

    return isEqual(annotation.shape, imageRoi);
};

const ensureAnomalyAnnotationsAreConsistent = (
    annotations: ReadonlyArray<Annotation>,
    selectedTask: Task,
    imageRoi: Rect
) => {
    // If the user only has a single global annotation then the same rules as classification applies
    if (annotations.length === 1 && isGlobalAnnotation(annotations[0], imageRoi)) {
        return ensureClassificationAnnotationsAreConsistent(annotations);
    }

    // Make sure that there is that if there are anomalous annotations, then there
    // should be a global anomalous annotation
    const anomalousLabel = selectedTask.labels.find(isAnomalous);

    if (anomalousLabel === undefined) {
        return annotations;
    }

    const globalAnnotation = annotations.find((annotation) => isGlobalAnnotation(annotation, imageRoi));

    if (globalAnnotation === undefined) {
        const newGlobalAnnotation = getLabeledShape(
            uuidv4(),
            imageRoi,
            [labelFromUser(anomalousLabel)],
            false,
            annotations.length
        );

        return [newGlobalAnnotation, ...annotations];
    }

    // If there is a global annotation, then we want to make sure that,
    // since there are local anomaous annotations, that it is given a anomalous label
    if (!globalAnnotation.labels.some(isAnomalous)) {
        return annotations.map((annotation) => {
            if (annotation.id === globalAnnotation.id) {
                return { ...annotation, labels: [labelFromUser(anomalousLabel)] };
            }
            return annotation;
        });
    }

    return annotations;
};

export const useEnsureAnnotationsAreValid = (): ((
    annotations: ReadonlyArray<Annotation>
) => ReadonlyArray<Annotation>) => {
    const { selectedTask, tasks } = useTask();
    const imageRoi = useImageROI();

    // Only enable this logic when not in a task chain
    if (selectedTask === null || tasks.length > 1) {
        return identity;
    }

    if (isClassificationDomain(selectedTask.domain)) {
        return ensureClassificationAnnotationsAreConsistent;
    }

    if (imageRoi !== undefined && isAnomalyDomain(selectedTask.domain)) {
        return (annotations) => ensureAnomalyAnnotationsAreConsistent(annotations, selectedTask, imageRoi);
    }

    return identity;
};
