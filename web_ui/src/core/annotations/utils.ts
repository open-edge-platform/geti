// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isNonEmptyArray } from '../../shared/utils';
import { Label } from '../labels/label.interface';
import { AnnotationStatePerTask, MEDIA_ANNOTATION_STATUS } from '../media/base.interface';
import { Task } from '../projects/task.interface';
import { Annotation, AnnotationLabel } from './annotation.interface';
import { isPointInShape } from './math';
import { Circle, Point, Polygon, Pose, Rect, RotatedRect, Shape } from './shapes.interface';
import { ShapeType } from './shapetype.enum';

export const MAX_SUPPORTED_ANNOTATIONS = 100000;
export const hasMaxAllowedAnnotations = (annotations: ReadonlyArray<Annotation>): boolean => {
    return annotations.length >= MAX_SUPPORTED_ANNOTATIONS;
};

export const isRect = (shape: Shape): shape is Rect => {
    return shape.shapeType === ShapeType.Rect;
};

export const isCircle = (shape: Shape): shape is Circle => {
    return shape.shapeType === ShapeType.Circle;
};

export const isPolygon = (shape: Shape): shape is Polygon => {
    return shape.shapeType === ShapeType.Polygon;
};

export const isRotatedRect = (shape: Shape): shape is RotatedRect => {
    return shape.shapeType === ShapeType.RotatedRect;
};

export const isPoseShape = (shape: Shape): shape is Pose => {
    return shape.shapeType === ShapeType.Pose;
};

export const labelFromUser = (label: Label, userId?: string): AnnotationLabel => {
    return { ...label, score: undefined, source: { userId } };
};

export const labelFromModel = (
    label: Label,
    score: number,
    modelId: string,
    modelStorageId: string
): AnnotationLabel => {
    return { ...label, source: { modelId, modelStorageId }, score };
};

const sortAnnotationsByIndex = (a: Annotation, b: Annotation): number => {
    return a.zIndex < b.zIndex ? 1 : -1;
};

export const getTheTopShapeAt = (
    annotations: ReadonlyArray<Annotation>,
    point: Point,
    checkInteractiveProps = true
): Annotation | null => {
    const intersectedAnnotations = annotations.filter((annotation: Annotation) => {
        const { isLocked, isHidden, shape } = annotation;
        if (checkInteractiveProps && (isHidden || isLocked)) {
            return false;
        }

        return isPointInShape(shape, point);
    });

    if (isNonEmptyArray(intersectedAnnotations)) {
        const sortedAnnotationsByIndex = [...intersectedAnnotations].sort(sortAnnotationsByIndex);

        return sortedAnnotationsByIndex[0];
    }

    return null;
};

export const getAnnotationStateForTask = (
    annotationStates: AnnotationStatePerTask[] = [],
    selectedTask: Task | null = null
): MEDIA_ANNOTATION_STATUS => {
    if (!annotationStates.length) {
        return MEDIA_ANNOTATION_STATUS.NONE;
    }

    if (selectedTask !== null) {
        const annotationStateForTask = annotationStates.find(({ taskId }) => taskId === selectedTask.id);

        return annotationStateForTask?.state ?? MEDIA_ANNOTATION_STATUS.NONE;
    }

    if (annotationStates.some(({ state }) => state === MEDIA_ANNOTATION_STATUS.TO_REVISIT)) {
        return MEDIA_ANNOTATION_STATUS.TO_REVISIT;
    }

    if (annotationStates.every(({ state }) => state === MEDIA_ANNOTATION_STATUS.ANNOTATED)) {
        return MEDIA_ANNOTATION_STATUS.ANNOTATED;
    } else if (annotationStates.every(({ state }) => state === MEDIA_ANNOTATION_STATUS.NONE)) {
        return MEDIA_ANNOTATION_STATUS.NONE;
    }

    return MEDIA_ANNOTATION_STATUS.PARTIALLY_ANNOTATED;
};
