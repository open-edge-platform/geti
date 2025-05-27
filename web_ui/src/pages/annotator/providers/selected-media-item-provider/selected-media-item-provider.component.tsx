// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useNavigateToAnnotatorRoute } from '@geti/core/src/services/use-navigate-to-annotator-route.hook';
import { getErrorMessage } from '@geti/core/src/services/utils';
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isEmpty, isEqual } from 'lodash-es';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { PredictionMode, PredictionResult } from '../../../../core/annotations/services/prediction-service.interface';
import { InferenceModel } from '../../../../core/annotations/services/visual-prompt-service';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { MediaItem } from '../../../../core/media/media.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { Task } from '../../../../core/projects/task.interface';
import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useUserProjectSettings } from '../../../../core/user-settings/hooks/use-project-settings.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { hasEqualId } from '../../../../shared/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useDatasetIdentifier } from '../../hooks/use-dataset-identifier.hook';
import { hasEmptyLabels } from '../../utils';
import { useTask } from '../task-provider/task-provider.component';
import { SelectedMediaItem } from './selected-media-item.interface';
import { useAnnotationsQuery } from './use-annotations-query.hook';
import { useLoadImageQuery } from './use-load-image-query.hook';
import { usePredictionsQuery } from './use-predictions-query.hook';
import { useSelectedInferenceModel } from './use-selected-inference-model';
import {
    constructClassificationAnnotations,
    getPendingMediaItem,
    useMediaIdentifierFromRoute,
    usePendingMediaItem,
} from './utils';

export interface SelectedMediaItemProps {
    predictionsQuery: UseQueryResult<PredictionResult>;
    selectedMediaItem: SelectedMediaItem | undefined;
    selectedMediaItemQuery: UseQueryResult<SelectedMediaItem>;
    setSelectedMediaItem: (media: MediaItem | undefined) => void;
}

export const SelectedMediaItemContext = createContext<SelectedMediaItemProps | undefined>(undefined);

const isNotAnnotatedForTask = (annotations: Annotation[], selectedTask: Task | null) => {
    if (isEmpty(annotations)) {
        return true;
    }

    if (selectedTask === null || !isClassificationDomain(selectedTask.domain)) {
        return false;
    }

    // Check if there is at least 1 annotation that does not contain a label from the selected task
    return annotations.some((annotation) => {
        if (hasEmptyLabels(annotation)) {
            return true;
        }

        return !annotation.labels.some((label) => selectedTask.labels.some(hasEqualId(label.id)));
    });
};

const usePredictionMode = () => {
    const [selectedModel] = useSelectedInferenceModel();
    const { isActiveLearningMode } = useAnnotatorMode();
    const { FEATURE_FLAG_VISUAL_PROMPT_SERVICE } = useFeatureFlags();

    if (FEATURE_FLAG_VISUAL_PROMPT_SERVICE && selectedModel === InferenceModel.VISUAL_PROMPT) {
        return PredictionMode.VISUAL_PROMPT;
    }

    return isActiveLearningMode ? PredictionMode.AUTO : PredictionMode.ONLINE;
};

const useIsSuggestPredictionEnabled = (projectIdentifier: ProjectIdentifier): boolean => {
    const settings = useUserProjectSettings(projectIdentifier);

    return settings.config[FEATURES_KEYS.INITIAL_PREDICTION].isEnabled;
};

/**
 * Load either online or auto predicitons based on the annotator mode
 * When the user switches between both modes we don't want to refetch predictions,
 * so in both cases we will keep the queries mounted
 */
const usePredictionsQueryBasedOnAnnotatorMode = (mediaItem: MediaItem | undefined) => {
    const datasetIdentifier = useDatasetIdentifier();
    const { isActiveLearningMode } = useAnnotatorMode();
    const { project, projectIdentifier } = useProject();
    const { selectedTask, isTaskChainSecondTask } = useTask();
    const { addNotification } = useNotification();

    const isSuggestPredictionsEnabled = useIsSuggestPredictionEnabled(projectIdentifier);

    const predictionMode = usePredictionMode();

    const predictionQueryOptions = {
        mediaItem,
        datasetIdentifier,
        taskId: selectedTask?.id,
        coreLabels: project.labels,
        onError: (error: AxiosError) => {
            if (predictionMode === PredictionMode.ONLINE) {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            }
        },
    };

    const { predictionsQuery: visualPromptPredictionsQuery } = usePredictionsQuery({
        enabled:
            isSuggestPredictionsEnabled && !isTaskChainSecondTask && predictionMode === PredictionMode.VISUAL_PROMPT,
        predictionId: PredictionMode.VISUAL_PROMPT,
        ...predictionQueryOptions,
    });

    const { predictionsQuery: onlinePredictionsQuery } = usePredictionsQuery({
        enabled: isSuggestPredictionsEnabled && !isTaskChainSecondTask && !isActiveLearningMode,
        predictionId: PredictionMode.ONLINE,
        ...predictionQueryOptions,
    });

    const { predictionsQuery: autoPredictionsQuery } = usePredictionsQuery({
        enabled: isSuggestPredictionsEnabled && !isTaskChainSecondTask && isActiveLearningMode,
        predictionId: PredictionMode.AUTO,
        ...predictionQueryOptions,
    });

    if (predictionMode === PredictionMode.VISUAL_PROMPT) {
        return visualPromptPredictionsQuery;
    }

    return isActiveLearningMode ? autoPredictionsQuery : onlinePredictionsQuery;
};

interface SelectedMediaItemProviderProps {
    children: ReactNode;
}

export const SelectedMediaItemProvider = ({ children }: SelectedMediaItemProviderProps): JSX.Element => {
    const { addNotification } = useNotification();
    const datasetIdentifier = useDatasetIdentifier();
    const { annotationService, router } = useApplicationServices();
    const mediaIdentifierFromRoute = useMediaIdentifierFromRoute();
    const { project, isSingleDomainProject } = useProject();
    const { selectedTask } = useTask();

    const navigate = useNavigateToAnnotatorRoute();

    const [selectedMediaItem, setSelectedMediaItem] = useState<SelectedMediaItem>();
    const [pendingMediaItem, setPendingMediaItem] = usePendingMediaItem(datasetIdentifier, selectedMediaItem);

    const mediaItem = getPendingMediaItem(datasetIdentifier, pendingMediaItem, router);

    const imageQuery = useLoadImageQuery(mediaItem);

    const annotationsQuery = useAnnotationsQuery({
        annotationService,
        coreLabels: project.labels,
        datasetIdentifier,
        mediaItem,
    });

    const predictionsQuery = usePredictionsQueryBasedOnAnnotatorMode(mediaItem);

    const selectedMediaItemQueryKey = [
        ...QUERY_KEYS.SELECTED_MEDIA_ITEM.SELECTED(pendingMediaItem?.identifier, selectedTask?.id),
        [imageQuery.fetchStatus, annotationsQuery.fetchStatus, predictionsQuery.fetchStatus],
    ];

    const isSelectedMediaItemQueryEnabled = mediaItem !== undefined;

    const selectedMediaItemQuery = useQuery<SelectedMediaItem>({
        queryKey: selectedMediaItemQueryKey,
        queryFn: async () => {
            if (mediaItem === undefined) {
                throw new Error("Can't fetch undefined media item");
            }

            const [image, annotations, predictions] = await new Promise<[ImageData, Annotation[], PredictionResult]>(
                (resolve, reject) => {
                    if (imageQuery.isError) {
                        reject({
                            message: 'Failed loading media item. Please try refreshing or selecting a different item.',
                        });
                    }

                    if (imageQuery.data && annotationsQuery.data) {
                        if (!predictionsQuery.data && predictionsQuery.isFetching) {
                            // If we do not yet have predictions and the user has not yet made any annotations
                            // for the selected task, then we will wait for predictions
                            if (isNotAnnotatedForTask(annotationsQuery.data, selectedTask)) {
                                return;
                            }
                        }

                        const predictionsData = predictionsQuery.data ?? { maps: [], annotations: [] };

                        resolve([imageQuery.data, annotationsQuery.data, predictionsData]);
                    }
                }
            );

            const newlySelectedMediaItem = { ...mediaItem, image, annotations, predictions };

            if (isSingleDomainProject(isClassificationDomain)) {
                return {
                    ...newlySelectedMediaItem,
                    annotations: constructClassificationAnnotations(newlySelectedMediaItem),
                };
            }

            return newlySelectedMediaItem;
        },
        enabled: isSelectedMediaItemQueryEnabled,
        gcTime: 0,
    });

    useEffect(() => {
        if (!selectedMediaItemQuery.isError) {
            return;
        }

        addNotification({
            message: 'Failed loading media item. Please try refreshing the page.',
            type: NOTIFICATION_TYPE.ERROR,
        });
    }, [selectedMediaItemQuery.isError, addNotification]);

    useEffect(() => {
        if (!isSelectedMediaItemQueryEnabled || !selectedMediaItemQuery.isSuccess) {
            return;
        }

        const item = selectedMediaItemQuery.data;

        setSelectedMediaItem(item);

        if (!isEqual(mediaIdentifierFromRoute, item.identifier)) {
            navigate({ datasetIdentifier, mediaItem: item });
        }
    }, [
        isSelectedMediaItemQueryEnabled,
        selectedMediaItemQuery.isSuccess,
        selectedMediaItemQuery.data,
        navigate,
        datasetIdentifier,
        mediaIdentifierFromRoute,
    ]);

    useEffect(() => {
        const hasNoMediaItemToDisplay =
            mediaIdentifierFromRoute === undefined && pendingMediaItem === undefined && selectedMediaItem !== undefined;

        if (hasNoMediaItemToDisplay) {
            setSelectedMediaItem(undefined);
        }
    }, [mediaIdentifierFromRoute, pendingMediaItem, selectedMediaItem]);

    const value: SelectedMediaItemProps = {
        predictionsQuery,
        selectedMediaItem,
        selectedMediaItemQuery,
        setSelectedMediaItem: setPendingMediaItem,
    };

    return <SelectedMediaItemContext.Provider value={value}>{children}</SelectedMediaItemContext.Provider>;
};

export const useSelectedMediaItem = (): SelectedMediaItemProps => {
    const context = useContext(SelectedMediaItemContext);

    if (context === undefined) {
        throw new MissingProviderError('useSelectedMediaItem', 'SelectedMediaItemProvider');
    }

    return context;
};
