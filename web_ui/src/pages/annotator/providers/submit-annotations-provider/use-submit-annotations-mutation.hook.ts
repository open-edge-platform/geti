// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MutableRefObject, useCallback, useRef } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import isEmpty from 'lodash/isEmpty';
import isFunction from 'lodash/isFunction';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getAnnotationStateForTask } from '../../../../core/annotations/utils';
import { MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
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
