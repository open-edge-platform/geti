// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, MutableRefObject, SetStateAction } from 'react';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { Shape } from '../../../core/annotations/shapes.interface';
import { Label } from '../../../core/labels/label.interface';

export interface AnnotationScene {
    readonly labels: ReadonlyArray<Label>;
    readonly annotations: ReadonlyArray<Annotation>;
    isDrawing: boolean;
    hasShapePointSelected: MutableRefObject<boolean>;

    setIsDrawing: Dispatch<SetStateAction<boolean>>;

    addShapes: (
        shapes: Shape[],
        annotationLabels?: Label[] | null,
        isSelected?: boolean,
        conflictResolver?: (label: Label, otherLabel: Label) => boolean
    ) => Annotation[];

    allAnnotationsHidden: boolean;

    addLabel: (
        label: Label,
        annotationIds: string[],
        conflictResolver?: (label: Label, otherLabel: Label) => boolean
    ) => void;
    removeLabels: (labels: Label[], annotationIds: string[], skipHistory?: boolean) => void;

    updateAnnotation: (annotation: Annotation) => void;
    removeAnnotations: (annotations: Annotation[], skipHistory?: boolean) => void;

    addAnnotations: (annotations: Annotation[]) => void;
    replaceAnnotations: (annotations: Annotation[], skipHistory?: boolean) => void;

    hoverAnnotation: (annotationId: string | null) => void;

    setSelectedAnnotations: (predicate: (annotation: Annotation) => boolean) => void;
    setLockedAnnotations: (predicate: (annotation: Annotation) => boolean) => void;
    setHiddenAnnotations: (predicate: (annotation: Annotation) => boolean) => void;

    selectAnnotation: (annotationId: string) => void;
    unselectAnnotation: (annotationId: string) => void;
    unselectAllAnnotations: () => void;

    toggleLock: (isLock: boolean, annotationId: string) => void;

    hideAnnotation: (annotationId: string) => void;
    showAnnotation: (annotationId: string) => void;
}
