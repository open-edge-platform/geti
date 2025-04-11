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
