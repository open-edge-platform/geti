// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty, negate } from 'lodash-es';

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
