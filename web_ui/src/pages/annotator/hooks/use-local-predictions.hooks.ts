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

import isEmpty from 'lodash/isEmpty';
import negate from 'lodash/negate';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { hasEqualBoundingBox } from '../../../core/annotations/math';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { isGlobal } from '../../../core/labels/utils';
import { useAnnotationFilters } from '../annotation/annotation-filter/use-annotation-filters.hook';
import { useIsPredictionRejected } from '../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { usePrediction } from '../providers/prediction-provider/prediction-provider.component';
import { useROI } from '../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useSelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item-provider.component';

const getAnnotationsLabelsFilter = (filters: string[]) => (annotation: Annotation) =>
    isEmpty(filters) ? true : annotation.labels.some(({ id }) => filters.includes(id));

// Returns predictions shown in the prediction list
export const useLocalPredictions = () => {
    const [filters] = useAnnotationFilters();
    const isPredictionRejected = useIsPredictionRejected();
    const { predictionsQuery, selectedMediaItemQuery } = useSelectedMediaItem();
    const { predictionsRoiQuery, predictionAnnotations } = usePrediction();

    const labelsFilter = getAnnotationsLabelsFilter(filters);
    const isPredictionAccepted = negate(isPredictionRejected);
    const { roi } = useROI();

    return {
        isLoading: predictionsRoiQuery.isPending || predictionsQuery.isPending || selectedMediaItemQuery.isPending,
        isFetching: predictionsRoiQuery.isFetching || predictionsQuery.isFetching,
        predictions: predictionAnnotations.filter((prediction) => {
            const hasGlobalLabel = prediction.labels.some(isGlobal);
            const isGlobalAnnotation =
                hasGlobalLabel &&
                prediction.shape.shapeType === ShapeType.Rect &&
                hasEqualBoundingBox(prediction.shape, roi);

            return isPredictionAccepted(prediction) && labelsFilter(prediction) && !isGlobalAnnotation;
        }),
    };
};
