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

import { useEffect, useRef, useState } from 'react';

import sortBy from 'lodash/sortBy';
import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Shape } from '../../../../core/annotations/shapes.interface';
import { labelFromUser } from '../../../../core/annotations/utils';
import { recursivelyAddLabel, recursivelyRemoveLabels } from '../../../../core/labels/label-resolver';
import { Label } from '../../../../core/labels/label.interface';
import { getIds, hasEqualId, isNonEmptyArray } from '../../../../shared/utils';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { UndoRedoActions } from '../../core/undo-redo-actions.interface';
import useUndoRedoState from '../../tools/undo-redo/use-undo-redo-state';
import { getLabeledShape } from '../../utils';

export const useAnnotationSceneState = (
    initialAnnotations: ReadonlyArray<Annotation>,
    labels: ReadonlyArray<Label>,
    activeUserId?: string | undefined
): AnnotationScene & { undoRedoActions: UndoRedoActions } => {
    const [annotations, setAnnotations, undoRedoActions] = useUndoRedoState(initialAnnotations);

    const resetAnnotations = undoRedoActions.reset;
    const hasShapePointSelected = useRef(false);
    const [isDrawing, setIsDrawing] = useState(false);

    useEffect(() => {
        resetAnnotations(initialAnnotations);
    }, [initialAnnotations, resetAnnotations]);

    const addShapes = (
        shapes: Shape[],
        annotationLabels?: Label[] | null,
        isSelected = true,
        conflictPredicate?: (label: Label, otherLabel: Label) => boolean
    ): Annotation[] => {
        const defaultLabels = isNonEmptyArray(annotationLabels)
            ? annotationLabels.map((iLabel) => recursivelyAddLabel([], iLabel, labels, conflictPredicate)).flat()
            : [];

        const userLabels = defaultLabels.map((annotationLabel) => labelFromUser(annotationLabel, activeUserId));

        const newAnnotations: Annotation[] = shapes.map((shape, idx) =>
            getLabeledShape(uuidv4(), shape, userLabels, isSelected, annotations.length + idx)
        );

        setAnnotations((prevAnnotations) => [...prevAnnotations, ...newAnnotations]);

        return newAnnotations;
    };

    const addAnnotations = (newAnnotations: Annotation[]) => {
        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            return [
                ...prevAnnotations.map((annotation) => {
                    return {
                        ...annotation,
                        isSelected: false,
                    };
                }),
                ...newAnnotations,
            ];
        });
    };

    const removeAnnotations = (predicate: Annotation[], skipHistory = false): void => {
        const ids = getIds(predicate);

        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            return prevAnnotations
                .filter(({ id }) => !ids.includes(id))
                .map((annotation, index) => ({ ...annotation, zIndex: index }));
        }, skipHistory);
    };

    const updateAnnotation = (annotation: Annotation): void => {
        setAnnotations((oldAnnotations: ReadonlyArray<Annotation>) => {
            return oldAnnotations.map((oldAnnotation: Annotation) => {
                return oldAnnotation.id === annotation.id ? annotation : oldAnnotation;
            });
        });
    };

    const replaceAnnotations = (newAnnotations: Annotation[], skipHistory = false): void => {
        setAnnotations(() => newAnnotations, skipHistory);
    };

    const addLabel = (
        label: Label,
        annotationIds: string[],
        conflictPredicate?: (label: Label, otherLabel: Label) => boolean
    ): void => {
        setAnnotations((newAnnotations: ReadonlyArray<Annotation>) => {
            return newAnnotations.map((annotation: Annotation) => {
                if (!annotationIds.includes(annotation.id)) {
                    return annotation;
                }

                const annotationLabels = sortBy(
                    recursivelyAddLabel(annotation.labels, label, labels, conflictPredicate).map((annotationLabel) =>
                        labelFromUser(annotationLabel, activeUserId)
                    ),
                    ({ id }) => labels.findIndex(hasEqualId(id))
                );

                return {
                    ...annotation,
                    labels: annotationLabels,
                };
            });
        });
    };

    const removeLabels = (labelToBeRemoved: Label[], annotationIds: string[], skipHistory = false): void => {
        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            return prevAnnotations.map((annotation: Annotation) => {
                if (!annotationIds.includes(annotation.id)) {
                    return annotation;
                }

                const annotationLabels = recursivelyRemoveLabels(annotation.labels, labelToBeRemoved).map(
                    (annotationLabel) => labelFromUser(annotationLabel)
                );

                return {
                    ...annotation,
                    labels: annotationLabels,
                };
            });
        }, skipHistory);
    };

    const hoverAnnotation = (annotationId: string | null): void => {
        setAnnotations(
            (prevAnnotations: ReadonlyArray<Annotation>) =>
                prevAnnotations.map((annotation) => ({ ...annotation, isHovered: annotation.id === annotationId })),
            true
        );
    };

    const selectAnnotation = (annotationId: string): void => {
        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            const newAnnotations = prevAnnotations.map((annotation: Annotation) =>
                annotation.id === annotationId ? { ...annotation, isSelected: true } : annotation
            );

            return newAnnotations;
        }, true);
    };

    const setSelectedAnnotations = (predicate: (annotation: Annotation) => boolean): void => {
        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            return prevAnnotations.map((annotation: Annotation) => {
                const isSelected = predicate(annotation);

                if (isSelected !== annotation.isSelected) {
                    return { ...annotation, isSelected };
                }

                return annotation;
            });
        }, true);
    };

    const setLockedAnnotations = (predicate: (annotation: Annotation) => boolean): void => {
        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            return prevAnnotations.map((annotation: Annotation) => {
                const isLocked = predicate(annotation);

                if (isLocked !== annotation.isLocked) {
                    return { ...annotation, isLocked };
                }

                return annotation;
            });
        }, true);
    };

    const setHiddenAnnotations = (predicate: (annotation: Annotation) => boolean): void => {
        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            return prevAnnotations.map((annotation: Annotation) => {
                const isHidden = predicate(annotation);

                if (isHidden !== annotation.isHidden) {
                    return { ...annotation, isHidden };
                }

                return annotation;
            });
        }, true);
    };

    const unselectAnnotation = (annotationId: string): void => {
        setAnnotations((prevAnnotations: ReadonlyArray<Annotation>) => {
            const newAnnotations = prevAnnotations.map((annotation: Annotation) =>
                annotation.id === annotationId ? { ...annotation, isSelected: false } : annotation
            );

            return newAnnotations;
        }, true);
    };

    const unselectAllAnnotations = (): void => {
        setAnnotations((prevAnnotations) =>
            prevAnnotations.map((annotation) => ({ ...annotation, isSelected: false }))
        );
    };

    const toggleLock = (shouldLock: boolean, annotationId: string): void => {
        setAnnotations(
            (prevAnnotations: ReadonlyArray<Annotation>) =>
                prevAnnotations.map((annotation) => {
                    if (annotation.id === annotationId) {
                        return { ...annotation, isLocked: shouldLock };
                    }

                    return annotation;
                }),
            true
        );
    };

    const hideAnnotation = (annotationId: string): void => {
        setAnnotations(
            (prevAnnotations: ReadonlyArray<Annotation>) =>
                prevAnnotations.map((annotation) => {
                    if (annotation.id === annotationId) {
                        return { ...annotation, isHidden: true };
                    }

                    return annotation;
                }),
            true
        );
    };

    const showAnnotation = (annotationId: string): void => {
        setAnnotations(
            (prevAnnotations: ReadonlyArray<Annotation>) =>
                prevAnnotations.map((annotation) => {
                    if (annotation.id === annotationId) {
                        return { ...annotation, isHidden: false };
                    }

                    return annotation;
                }),
            true
        );
    };

    const allAnnotationsHidden = !annotations.find((annotation: Annotation) => !annotation.isHidden);

    return {
        annotations,
        labels,
        isDrawing,

        addShapes,
        setIsDrawing,

        addLabel,
        allAnnotationsHidden,

        removeLabels,
        addAnnotations,
        removeAnnotations,
        updateAnnotation,
        replaceAnnotations,

        hoverAnnotation,

        setSelectedAnnotations,
        setLockedAnnotations,
        setHiddenAnnotations,

        selectAnnotation,
        unselectAnnotation,
        unselectAllAnnotations,

        toggleLock,

        hideAnnotation,
        showAnnotation,
        hasShapePointSelected,

        undoRedoActions,
    };
};
