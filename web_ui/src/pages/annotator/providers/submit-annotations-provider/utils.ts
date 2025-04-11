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

import isEmpty from 'lodash/isEmpty';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { areAnnotationsIdentical, hasValidLabels, isUserAnnotation } from '../../utils';

export const shouldSaveAnnotations = (
    annotations: Annotation[] | undefined,
    newAnnotations: ReadonlyArray<Annotation>
): boolean => {
    if (annotations === undefined) {
        return false;
    }

    return !areAnnotationsIdentical(annotations, newAnnotations);
};

export const hasMediaPredictionChanges = (
    annotations: Annotation[] | undefined,
    predictionsAsInitialAnnotations: readonly Annotation[] | undefined,
    newAnnotations: ReadonlyArray<Annotation>
): boolean => {
    if (annotations === undefined) {
        return false;
    }

    const hasAnnotations = !isEmpty(newAnnotations);
    const hasPredictionsAsInitialAnnotations = !isEmpty(predictionsAsInitialAnnotations);

    // Note: for classification projects we add a global annotation without any labels,
    // in this case we ignore this annotation
    const isSavedAnnotationsEmpty = isEmpty(annotations?.filter(hasValidLabels));

    if (hasAnnotations && hasPredictionsAsInitialAnnotations && isSavedAnnotationsEmpty) {
        return !areAnnotationsIdentical(predictionsAsInitialAnnotations, newAnnotations);
    }

    // We only want to show a confirmation message if the user manually made changes,
    // therefore we will remove any predicted filters so that we don't check show a
    // confirmation message if the user loaded any predictions
    const annotationsWithoutPredictedLabels = newAnnotations.map((annotation) => ({
        ...annotation,
        labels: annotation.labels.filter(isUserAnnotation),
    }));

    return shouldSaveAnnotations(annotations, annotationsWithoutPredictedLabels);
};
