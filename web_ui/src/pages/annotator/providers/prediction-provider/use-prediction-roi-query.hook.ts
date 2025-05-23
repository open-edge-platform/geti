// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useLayoutEffect, useRef } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { TaskChainInput } from '../../../../core/annotations/annotation.interface';
import {
    PredictionCache,
    PredictionMode,
    PredictionResult,
} from '../../../../core/annotations/services/prediction-service.interface';
import { getPredictionCache } from '../../../../core/annotations/services/utils';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { usePrevious } from '../../../../hooks/use-previous/use-previous.hook';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useDatasetIdentifier } from '../../hooks/use-dataset-identifier.hook';
import { useSelectedMediaItem } from '../selected-media-item-provider/selected-media-item-provider.component';

interface usePredictionsRoiQueryProps {
    taskId: string;
    enabled?: boolean;
    selectedInput: TaskChainInput;
    onSuccess?: (response: PredictionResult) => void;
}

export const usePredictionsRoiQuery = ({
    taskId,
    selectedInput,
    enabled = true,
    onSuccess,
}: usePredictionsRoiQueryProps) => {
    const roiId = selectedInput?.id;
    const prevRoi = usePrevious(roiId);
    const { project } = useProject();
    const { isActiveLearningMode } = useAnnotatorMode();

    // TODO: this may not be right, i.e. if the user changes dataset
    const datasetIdentifier = useDatasetIdentifier();
    const { selectedMediaItem } = useSelectedMediaItem();
    const { inferenceService } = useApplicationServices();

    const isValidRoi = roiId !== undefined && prevRoi !== roiId;

    const isQueryEnabled = enabled && isValidRoi;

    const predictionMode = isActiveLearningMode ? PredictionMode.AUTO : PredictionMode.ONLINE;
    const predictionCache = getPredictionCache(predictionMode);
    const isPredictionCacheNever = predictionCache === PredictionCache.NEVER;

    const handleSuccessRef = useRef(onSuccess);

    useLayoutEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    // TODO: extract explanation, combine with other prediction query

    const query = useQuery<PredictionResult, AxiosError>({
        queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.PREDICTIONS(
            selectedMediaItem?.identifier,
            'prediction-roi',
            predictionCache,
            taskId,
            roiId
        ),
        queryFn: async ({ signal }) => {
            if (isQueryEnabled === false) {
                return { maps: [], annotations: [] };
            }

            if (selectedMediaItem === undefined) {
                return { maps: [], annotations: [] };
            }

            const explainPromise = isPredictionCacheNever
                ? inferenceService.getExplanations(datasetIdentifier, selectedMediaItem, taskId, selectedInput, signal)
                : Promise.resolve([]);

            return Promise.allSettled([
                inferenceService.getPredictions(
                    datasetIdentifier,
                    project.labels,
                    selectedMediaItem,
                    predictionCache,
                    taskId,
                    selectedInput,
                    signal
                ),
                explainPromise,
            ]).then(([annotationsResponse, mapsResponse]) => {
                const maps = mapsResponse.status === 'fulfilled' ? mapsResponse.value : [];
                const annotations = annotationsResponse.status === 'fulfilled' ? annotationsResponse.value : [];

                handleSuccessRef.current !== undefined && handleSuccessRef.current({ annotations, maps });

                return { annotations, maps };
            });
        },
        initialData: { maps: [], annotations: [] },
        enabled: isQueryEnabled,
    });

    return query;
};
