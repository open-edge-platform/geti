// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MutableRefObject, useCallback, useRef } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isEmpty, isFunction } from 'lodash-es';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getAnnotationStateForTask } from '../../../../core/annotations/utils';
import { MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import { useFuxNotifications } from '../../../../hooks/use-fux-notifications/use-fux-notifications.hook';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { useCollectAnnotatorMetrics } from '../../analytics-hooks/use-collect-annotator-metrics.hook';
import { hasInvalidAnnotations } from '../../utils';
import { SelectedMediaItem } from '../selected-media-item-provider/selected-media-item.interface';
import { SaveAnnotationMutation, UseSubmitAnnotationsMutationResult } from './submit-annotations.interface';
import { useEnsureAnnotationsAreValid } from './use-ensure-annotations-are-valid';
import { shouldSaveAnnotations } from './utils';

// If the specific annotations have been provided, which may happen in case the
// user has chosen to remove invalid annotations or add empty annotations, use
// these otherwise the user's (unfinished) annotations are used.
const getAnnotationsToSave = (
    annotations: ReadonlyArray<Annotation>,
    unfinishedShapesCallback: UnfinishedShapesCallback
) => {
    return isFunction(unfinishedShapesCallback) ? unfinishedShapesCallback() : annotations;
};

type UnfinishedShapesCallback = (() => Annotation[]) | null;
interface UseSubmitAnnotationsMutation {
    submitAnnotationsMutation: UseSubmitAnnotationsMutationResult;
    afterSaving: MutableRefObject<(() => Promise<void>) | undefined>;
    unfinishedShapesCallback: MutableRefObject<UnfinishedShapesCallback>;
    callCallbackAndClear: () => void;
}

export const useSubmitAnnotationsMutation = (
    mediaItem: SelectedMediaItem | undefined,
    setShowFailDialog: (showFailDialog: boolean) => void,
    setShowConfirmationDialog: (showConfirmationDialog: boolean) => void,
    saveAnnotations: (annotations: ReadonlyArray<Annotation>) => Promise<void>
): UseSubmitAnnotationsMutation => {
    // This callback is used to return a user's unfinished annotations, which
    // is used by quick selection and object coloring
    const unfinishedShapesCallback = useRef<UnfinishedShapesCallback>(null);

    const client = useQueryClient();
    const afterSaving = useRef<() => Promise<void>>();
    const projectIdentifier = useProjectIdentifier();
    const ensureAnnotationsAreValid = useEnsureAnnotationsAreValid();
    const { collectPredictionsMetric, collectToolsFrequencyMetric } = useCollectAnnotatorMetrics();
    const { handleFirstAnnotation } = useFuxNotifications();

    const hasLabelsToRevisit =
        getAnnotationStateForTask(mediaItem?.annotationStatePerTask) === MEDIA_ANNOTATION_STATUS.TO_REVISIT;

    const callCallbackAndClear = useCallback(() => {
        if (afterSaving.current) {
            const callback = afterSaving.current;

            afterSaving.current = undefined;

            callback();
        }
    }, []);

    const submitAnnotationsMutation = useMutation<void, AxiosError, SaveAnnotationMutation>({
        mutationFn: async ({ annotations, callback }: SaveAnnotationMutation) => {
            const annotationsToSave = ensureAnnotationsAreValid(
                getAnnotationsToSave(annotations, unfinishedShapesCallback.current)
            );

            if (isFunction(callback)) {
                afterSaving.current = callback;
            }

            if (hasInvalidAnnotations(annotationsToSave)) {
                setShowFailDialog(true);

                return;
            }
            const containsChanges = shouldSaveAnnotations(mediaItem?.annotations, annotationsToSave);

            if (containsChanges || hasLabelsToRevisit) {
                collectToolsFrequencyMetric();

                const originalPredictions = mediaItem?.predictions?.annotations ?? [];
                if (!isEmpty(originalPredictions)) {
                    collectPredictionsMetric(originalPredictions, [...annotationsToSave]);
                }

                await saveAnnotations(annotationsToSave);
                handleFirstAnnotation();
            }

            callCallbackAndClear();
            setShowConfirmationDialog(false);
            setShowFailDialog(false);
        },

        onSuccess: async () => {
            await client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_STATUS_KEY(projectIdentifier) });
        },
    });

    return {
        afterSaving,
        callCallbackAndClear,
        unfinishedShapesCallback,
        submitAnnotationsMutation,
    };
};
