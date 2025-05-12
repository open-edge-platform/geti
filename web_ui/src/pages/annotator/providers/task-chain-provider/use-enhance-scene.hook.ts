// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import intersectionBy from 'lodash/intersectionBy';
import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';
import negate from 'lodash/negate';
import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getBoundingBox, getCenterOfShape, hasEqualBoundingBox } from '../../../../core/annotations/math';
import { Rect, Shape } from '../../../../core/annotations/shapes.interface';
import { isRect, labelFromUser } from '../../../../core/annotations/utils';
import { Label } from '../../../../core/labels/label.interface';
import { isAnomalous, isExclusive, isGlobal } from '../../../../core/labels/utils';
import { isAnomalyDomain, isClassificationDomain, isDetectionDomain } from '../../../../core/projects/domains';
import { Task } from '../../../../core/projects/task.interface';
import { getIds, hasEqualId, isNonEmptyArray } from '../../../../shared/utils';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { useImageROI } from '../../hooks/use-image-roi.hook';
import { isPointWithinRoi } from '../../tools/geometry-utils';
import {
    containsGlobalAnnotationWithLabel,
    getAnnotationsWithSelectedInput,
    getGlobalAnnotations,
    getGlobalAnnotationsWithoutLabels,
    getInputForTask,
    getLabelConflictPredicate,
    getPreviousTask,
    getSelectedInputAnnotations,
    possiblyAddGlobalAnomalousShape,
} from './utils';

export const useEnhanceScene = (
    parentScene: AnnotationScene,
    tasks: Task[],
    selectedTask: Task | null,
    defaultLabel: Label | null
) => {
    const imageRoi = useImageROI();

    const inputAnnotations = useMemo(
        () => getInputForTask(parentScene.annotations, tasks, selectedTask),
        [parentScene, tasks, selectedTask]
    );

    const scene: AnnotationScene = useMemo((): AnnotationScene => {
        const annotations = getAnnotationsWithSelectedInput(parentScene.annotations, inputAnnotations);

        const removeEmptyAnnotations = (shapes: Shape[], labels: Label[] | null) => {
            // Determine if this annotation is placed inside of another annotation, that has
            // an empty label from the same task
            const boundingBoxes = shapes.map(getCenterOfShape);
            const emptyAnnotations = annotations.filter(({ labels: annotationsLabels, shape }) => {
                if (!annotationsLabels.some(isExclusive)) {
                    return false;
                }

                const emptyBoundingBox = getBoundingBox(shape);

                return boundingBoxes.some((center) => isPointWithinRoi(emptyBoundingBox, center));
            });

            emptyAnnotations.forEach((emptyAnnotation) => {
                if (emptyAnnotation.labels.length === 1) {
                    parentScene.removeAnnotations([emptyAnnotation], true);
                } else {
                    const anomalousLabels = labels?.filter(isAnomalous);
                    if (isNonEmptyArray(anomalousLabels)) {
                        anomalousLabels.forEach((label) => parentScene.addLabel(label, [emptyAnnotation.id]));
                    } else {
                        parentScene.removeLabels(
                            emptyAnnotation.labels.filter(isExclusive),
                            [emptyAnnotation.id],
                            true
                        );
                    }
                }
            });
        };

        const addShapes = (shapes: Shape[], rawLabels?: Label[] | null, isSelected = true): Annotation[] => {
            const validDefaultLabel = defaultLabel ? [defaultLabel] : [];
            let newLabels = isNonEmptyArray(rawLabels) ? rawLabels : validDefaultLabel;

            removeEmptyAnnotations(shapes, newLabels);

            // NOTE: here we can add some validation for the label, i.e. if it is a detection label,
            // then don't assign it to shapes if they are not rectangles
            const isDetectionLabel = tasks.some(
                ({ labels, domain }) => isDetectionDomain(domain) && !isEmpty(intersectionBy(labels, newLabels, 'id'))
            );

            const isNonDetectionShape = shapes.some(negate(isRect));

            if (isDetectionLabel && isNonDetectionShape) {
                newLabels = [];
            }

            // Make sure the previously selected annotations from the previous task stay selected
            const selectedInputAnnotations = getSelectedInputAnnotations(annotations, inputAnnotations);
            // Add shape and select old annotations
            const newAnnotations = parentScene.addShapes(
                possiblyAddGlobalAnomalousShape(shapes, newLabels, annotations, imageRoi),
                newLabels,
                isSelected,
                getLabelConflictPredicate(tasks)
            );

            const extraAnomalousAnnotationWasAdded = newAnnotations.length > shapes.length;

            if (extraAnomalousAnnotationWasAdded && imageRoi !== undefined) {
                // Remove any global annotations that do not have a label
                const globalAnnotationsWithoutLabel = getGlobalAnnotationsWithoutLabels(annotations, imageRoi);

                parentScene.removeAnnotations(globalAnnotationsWithoutLabel, true);
            }

            // Make sure that only the annotations added by the user will be selected
            const check = extraAnomalousAnnotationWasAdded ? [...newAnnotations].splice(1) : newAnnotations;

            parentScene.setSelectedAnnotations((annotation) => {
                if (selectedInputAnnotations.some(hasEqualId(annotation.id))) {
                    return true;
                }

                if (check.find(hasEqualId(annotation.id))) {
                    return annotation.isSelected;
                }

                return false;
            });

            return newAnnotations;
        };

        const addAnnotations = (newAnnotations: Annotation[]) => {
            // Determine if this annotation is placed inside another annotation, that has
            // an empty label from the same task
            const boundingBoxes = annotations.map(({ shape }) => shape).map(getCenterOfShape);
            const emptyAnnotations = annotations.filter(({ labels, shape }) => {
                if (labels.some(isAnomalous)) {
                    return false;
                }

                if (!labels.some(isExclusive) && !labels.some(isAnomalous)) {
                    return false;
                }

                const emptyBoundingBox = getBoundingBox(shape);

                return boundingBoxes.some((center) => isPointWithinRoi(emptyBoundingBox, center));
            });

            emptyAnnotations.forEach((emptyAnnotation) => {
                if (emptyAnnotation.labels.length === 1) {
                    // We want to remove the empty label, but since this means
                    // that this annotation has no label left, we will remove it instead
                    parentScene.removeAnnotations([emptyAnnotation], true);
                } else {
                    // Remove the empty label from the annotation
                    parentScene.removeLabels(emptyAnnotation.labels.filter(isExclusive), [emptyAnnotation.id], true);
                }
            });

            if (selectedTask === null || !isAnomalyDomain(selectedTask.domain)) {
                parentScene.addAnnotations(newAnnotations);
            } else {
                // We assume that any global empty or global anomalous annotations were removed in the previous steps,
                // so now we need to add the new global anomalous annotation
                const anomalousLabel = selectedTask.labels.find(isAnomalous);

                if (anomalousLabel && imageRoi !== undefined) {
                    const hasGlobalAnomalousAnnotation = annotations.some((annotation) => {
                        if (annotation.labels.some(hasEqualId(anomalousLabel.id))) {
                            return isRect(annotation.shape) && hasEqualBoundingBox(annotation.shape, imageRoi);
                        }
                    });

                    if (hasGlobalAnomalousAnnotation) {
                        parentScene.addAnnotations(newAnnotations);
                    } else {
                        // Add a global anomalous annotation
                        const newerAnnotations: Annotation[] = [
                            {
                                id: uuidv4(),
                                labels: [labelFromUser(anomalousLabel)],
                                shape: imageRoi,
                                zIndex: 0,
                                isHidden: false,
                                isLocked: false,
                                isSelected: false,
                            },
                            ...newAnnotations,
                        ];
                        parentScene.addAnnotations(newerAnnotations);
                    }
                }
            }

            // Make sure the previously selected annotations from the previous task stay selected
            const selectedInputAnnotations = getSelectedInputAnnotations(annotations, inputAnnotations);
            parentScene.setSelectedAnnotations((annotation) => {
                if (selectedInputAnnotations.some(hasEqualId(annotation.id))) {
                    return true;
                }

                const isNewAnnotation = newAnnotations.find(hasEqualId(annotation.id));

                if (isNewAnnotation !== undefined) {
                    return isNewAnnotation.isSelected;
                }

                return annotation.isSelected;
            });
        };

        const removeAnnotationsInsideOfROIs = (rois: Omit<Rect, 'shapeType'>[], excludeIds: string[]) => {
            const annotationsToBeRemoved: Annotation[] = annotations.filter((annotation) => {
                if (excludeIds.includes(annotation.id)) {
                    return false;
                }

                const center = getCenterOfShape(annotation.shape);

                return rois.some((roi) => isPointWithinRoi(roi, center));
            });

            if (!isEmpty(annotationsToBeRemoved)) {
                parentScene.removeAnnotations(annotationsToBeRemoved, true);
            }
        };

        const addEmptyLabelToAnnotations = (label: Label, annotationIds: string[]) => {
            const emptyRois = annotationIds
                .map((annotationId) => {
                    const annotation = annotations.find(hasEqualId(annotationId));

                    if (!annotation) {
                        return undefined;
                    }

                    return getBoundingBox(annotation.shape);
                })
                .filter((x): x is Omit<Rect, 'shapeType'> => x !== undefined);

            removeAnnotationsInsideOfROIs(emptyRois, annotationIds);

            parentScene.addLabel(label, annotationIds, getLabelConflictPredicate(tasks));
        };

        const addLabel = (label: Label, annotationIds: string[]) => {
            const isDetectionLabel = tasks.some(
                ({ labels, domain }) => isDetectionDomain(domain) && labels.some(hasEqualId(label?.id))
            );

            // If we're adding a detection label then the label is only allowed to be added to a Rect shape
            const validAnnotationIds = annotationIds.filter((annotationId) => {
                return !isDetectionLabel
                    ? true
                    : annotations.some(({ id, shape }) => id === annotationId && isRect(shape));
            });

            if (!isExclusive(label) && !isEmpty(annotationIds)) {
                parentScene.addLabel(label, validAnnotationIds, getLabelConflictPredicate(tasks));
                return;
            }

            // If the empy label comes from a sub task then it's likely that the user intended to add it
            // to an existing annotation, otherwise we assume they intended to add it to a selected input
            if (selectedTask === null) {
                const task = tasks.find(({ labels }) => labels.some(hasEqualId(label.id)));

                if (task !== tasks[0]) {
                    addEmptyLabelToAnnotations(label, validAnnotationIds);
                    return;
                }
            }

            // Dealing with empty labels in a local task is special, because the empty labels
            // are a "global" label, hence we either need apply it to a selected input (in case of task chain),
            // or we if there is no input we create a new shape with the image ROI
            const selectedInputAnnotations = getSelectedInputAnnotations(annotations, inputAnnotations);

            if (!isEmpty(selectedInputAnnotations)) {
                addEmptyLabelToAnnotations(label, getIds([...selectedInputAnnotations]));
                return;
            }

            // If no input annotation was selected, we add an empty label to the image ROI, but only,
            // if this task doesn't follow another task
            const previousTask = getPreviousTask(tasks, selectedTask);
            if (!isNil(previousTask)) {
                return;
            }

            if (!isGlobal(label)) {
                return;
            }

            if (containsGlobalAnnotationWithLabel(annotations, label, imageRoi)) {
                return;
            }

            const shapes = imageRoi !== undefined ? [imageRoi] : [];

            // Don't remove annotations that have the same label,
            // this prevents local anomalous annotations being removed when adding
            // a global anomalous annotation
            const nonConflictingAnnotations = getIds(
                annotations.filter(({ labels }) => labels.some(hasEqualId(label.id)))
            );

            removeAnnotationsInsideOfROIs(shapes, nonConflictingAnnotations);
            addShapes(shapes, [label]);
        };

        const selectAnnotation = (annotationId: string) => {
            // if it is an input annotation, toggle, otherwise do normal
            const isInputAnnotation = inputAnnotations.some(hasEqualId(annotationId));

            if (!isInputAnnotation) {
                parentScene.selectAnnotation(annotationId);
            } else {
                // Also: if inputAnnotations.some(({ id, isSelected }) => id === annotationId && isSelected) return;
                parentScene.setSelectedAnnotations((annotation) => {
                    if (annotation.id === annotationId) {
                        return true;
                    }

                    // Deselect any other input annotations
                    if (inputAnnotations.some(hasEqualId(annotation.id))) {
                        return false;
                    }

                    // Don't mutate this task's output selection state
                    return annotation.isSelected;
                });
            }
        };

        const removeAnnotations: AnnotationScene['removeAnnotations'] = (predicate, skipHistory = false) => {
            if (
                selectedTask === null ||
                (!isClassificationDomain(selectedTask.domain) && !isAnomalyDomain(selectedTask.domain))
            ) {
                parentScene.removeAnnotations(predicate, skipHistory);
                return;
            }

            // use this for a more refined roi?
            // const selectedInputAnnotations = getSelectedInputAnnotations(annotations, inputAnnotations);
            const roi = imageRoi as Rect;
            const globalAnnotations = getGlobalAnnotations(annotations, roi, selectedTask);

            const annotationsThatAreAllowedToBeRemoved = predicate.filter((annotation) => {
                return !globalAnnotations.some(hasEqualId(annotation.id));
            });

            parentScene.removeAnnotations(annotationsThatAreAllowedToBeRemoved, skipHistory);
        };

        return {
            ...parentScene,

            // Add additional task chain behavior
            selectAnnotation,
            addShapes,
            addAnnotations,
            addLabel,
            annotations,
            removeAnnotations,
        };
    }, [parentScene, inputAnnotations, tasks, imageRoi, selectedTask, defaultLabel]);

    return scene;
};
