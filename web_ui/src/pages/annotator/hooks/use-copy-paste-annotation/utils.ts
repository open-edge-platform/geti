// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import intersectionBy from 'lodash/intersectionBy';
import isEmpty from 'lodash/isEmpty';
import isObject from 'lodash/isObject';

import { Annotation, AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { Point } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';

const hasValidAnnotationStructure = (annotation: Annotation): boolean =>
    isObject(annotation) && ['id', 'labels', 'shape'].every((name) => annotation.hasOwnProperty(name));

const hasValidLabels = (validLabels: Label[], annotationLabels: readonly AnnotationLabel[]): boolean =>
    !isEmpty(annotationLabels) ? !isEmpty(intersectionBy(annotationLabels, validLabels, 'id')) : true;

export const hasValidLabelsAndStructure = (taskLabels: Label[], annotation: Annotation) =>
    hasValidAnnotationStructure(annotation) && hasValidLabels(taskLabels, annotation.labels);

export const getTranslateVector = ({ x, y }: Point, width: number, height: number, offset: number): Point => {
    const middleX = width / 2;
    const middleY = height / 2;

    // TOP LEFT QUARTER
    if (x < middleX && y < middleY) {
        return {
            x: offset,
            y: offset,
        };
    }

    // TOP RIGHT QUARTER
    if (x > middleX && y < middleY) {
        return {
            x: -offset,
            y: offset,
        };
    }

    // BOTTOM RIGHT QUARTER
    if (x > middleX && y > middleY) {
        return {
            x: -offset,
            y: -offset,
        };
    }

    // BOTTOM LEFT QUARTER
    return {
        x: offset,
        y: -offset,
    };
};
