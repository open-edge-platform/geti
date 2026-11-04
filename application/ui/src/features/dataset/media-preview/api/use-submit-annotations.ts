// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import { $api } from '@/api';
import type { AnnotationDTO, DatasetSubset, Media } from '@/api/types';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEqual } from 'lodash-es';

import {
    useAnnotationCommands,
    useAnnotations,
} from '../../../../modules/annotator/annotation-document-provider.component';
import {
    mapLocalAnnotationsToServer,
    mapServerAnnotationsToLocal,
} from '../../../../modules/annotator/annotation-mappers';
import { isEmptyLabel, isNonEmptyLabel, useProjectLabelsWithEmptyLabel } from '../../../../shared/labels';
import { getMediaItemQueryParams, isVideoFrame } from '../../../../shared/media-item-utils';
import type { Annotation } from '../../../../shared/types';
import { isNonEmptyArray } from '../../../../shared/util';
import {
    invalidateMediaFilteredByAnnotations,
    markCachedMediaAsAnnotated,
    refreshCachedMedia,
} from './update-cached-dataset-media';

const filterOutAnnotationWithEmptyLabel = (annotations: Annotation[]): Annotation[] => {
    return annotations.filter((annotation) => annotation.labels.some(isNonEmptyLabel));
};

const useSaveAnnotationsMutation = (mediaItem: Media) => {
    const projectId = useProjectIdentifier();
    const queryClient = useQueryClient();

    return $api.useMutation('post', '/api/projects/{project_id}/dataset/media/{media_id}/annotations', {
        meta: {
            invalidateQueries: [
                [
                    'get',
                    '/api/projects/{project_id}/dataset/media/{media_id}/annotations',
                    { params: { path: { project_id: projectId, media_id: mediaItem.id } } },
                ],
                [
                    'get',
                    '/api/projects/{project_id}/dataset/items/{dataset_item_id}',
                    { params: { path: { project_id: projectId, dataset_item_id: mediaItem.id } } },
                ],
                [
                    'get',
                    '/api/projects/{project_id}/dataset/media/{media_id}/frames',
                    { params: { path: { project_id: projectId, media_id: mediaItem.id } } },
                ],
            ],
        },
        onSuccess: async () => {
            // Not awaited: the submission must not wait for every loaded page of the filtered listings
            void invalidateMediaFilteredByAnnotations(queryClient, projectId);

            // The dataset media listing backs the gallery and sidebar annotation-status badges. Instead of
            // invalidating it (which would refetch every page already scrolled through), patch the cached media.
            if (isVideoFrame(mediaItem)) {
                // Frames share their video's id. Whether this frame was annotated before is unknown, so the video's
                // annotated frame count is fetched again. Awaited, so that saving stays pending (and the next save
                // disabled) until then: refreshes cannot overlap and resolve out of order. A failed refresh does not
                // fail the (successful) save: the count is only stale until the next listing.
                await refreshCachedMedia(queryClient, projectId, mediaItem.id).catch(() => undefined);
            } else {
                markCachedMediaAsAnnotated(queryClient, projectId, mediaItem.id);
            }
        },
    });
};

export const useSubmitAnnotations = ({
    mediaItem,
    hasSubsetChanged = false,
}: {
    mediaItem: Media;
    hasSubsetChanged?: boolean;
}) => {
    const projectId = useProjectIdentifier();
    const projectLabels = useProjectLabelsWithEmptyLabel();
    const { mode, annotations, initialAnnotations, initialPredictions } = useAnnotations();
    const { resetAnnotations } = useAnnotationCommands();
    const saveMutation = useSaveAnnotationsMutation(mediaItem);

    // In prediction mode `annotations` holds the predictions, so the user's edits are only read in annotation mode.
    const isPredictionMode = mode === 'prediction';

    const saveAnnotations = async (annotationsDTO: AnnotationDTO[], subset: DatasetSubset) => {
        await saveMutation.mutateAsync({
            params: {
                path: { media_id: mediaItem.id, project_id: projectId },
                query: getMediaItemQueryParams(mediaItem),
            },
            body: { annotations: annotationsDTO, subset },
        });

        resetAnnotations(mapServerAnnotationsToLocal(annotationsDTO));
    };

    const submit = async (subset: DatasetSubset) => {
        const validLabelIds = new Set(projectLabels.map((label) => label.id));

        if (isPredictionMode) {
            const predictionsWithoutConfidences = mapLocalAnnotationsToServer(initialPredictions, validLabelIds)
                .map(({ confidences, ...restOfAnnotation }) => restOfAnnotation)
                .filter((annotation) => isNonEmptyArray(annotation.labels) && annotation.labels.every(isNonEmptyLabel));

            await saveAnnotations(predictionsWithoutConfidences, subset);

            return;
        }

        await saveAnnotations(
            mapLocalAnnotationsToServer(filterOutAnnotationWithEmptyLabel(annotations), validLabelIds),
            subset
        );
    };

    const initialServerAnnotations = useMemo(
        () => mapLocalAnnotationsToServer(initialAnnotations),
        [initialAnnotations]
    );

    // Only the current side drops empty-label annotations: removing a saved "empty" label counts as a change.
    const hasChangedAnnotations = useMemo(
        () =>
            !isEqual(
                mapLocalAnnotationsToServer(filterOutAnnotationWithEmptyLabel(annotations)),
                initialServerAnnotations
            ),
        [annotations, initialServerAnnotations]
    );

    const hasEmptyLabelSelection = annotations.some((annotation) => annotation.labels.some(isEmptyLabel));
    const hasInvalidAnnotation = !isPredictionMode && annotations.some((annotation) => annotation.labels.length === 0);

    const canSubmit = isPredictionMode
        ? initialPredictions.length > 0
        : !hasInvalidAnnotation && (hasChangedAnnotations || hasEmptyLabelSelection || hasSubsetChanged);

    return {
        canSubmit,
        hasInvalidAnnotation,
        isSaving: saveMutation.isPending,
        submit,
    };
};
