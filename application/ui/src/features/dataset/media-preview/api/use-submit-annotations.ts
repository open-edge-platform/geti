// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import { $api } from '@/api';
import type { AnnotationDTO, DatasetItem, DatasetSubset, Media } from '@/api/types';
import { InfiniteData, matchQuery, useQueryClient } from '@tanstack/react-query';
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
import type { AnnotatorMode } from '../../../../modules/annotator/annotator-mode';
import { incrementCachedAnnotatedFrameCount } from '../../../../modules/annotator/utils';
import { getQueryKey } from '../../../../query-client/query-client';
import { EMPTY_LABEL_ID, isNonEmptyLabel, useProjectLabelsWithEmptyLabel } from '../../../../shared/labels';
import { isVideoFrame } from '../../../../shared/media-item-utils';
import type { Annotation } from '../../../../shared/types';
import { isNonEmptyArray } from '../../../../shared/util';

type DatasetItemsPage = { items: DatasetItem[] };

const filterOutAnnotationWithEmptyLabel = (annotations: Annotation[]): Annotation[] => {
    return annotations.filter((annotation) => annotation.labels.some((label) => label.id !== EMPTY_LABEL_ID));
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
        onSuccess: (data) => {
            // The dataset item list backs the sidebar's review-status badges. Instead of
            // invalidating it over the network (which would refetch every page the user has
            // already scrolled through - potentially dozens of requests on every single
            // submit), patch the affected item directly in the already-cached pages.
            const datasetItemsQueryKey = getQueryKey([
                'get',
                '/api/projects/{project_id}/dataset/items',
                { params: { path: { project_id: projectId } } },
            ]);

            queryClient.setQueriesData<InfiniteData<DatasetItemsPage>>(
                { predicate: (query) => matchQuery({ queryKey: datasetItemsQueryKey }, query) },
                (previousData) => {
                    if (previousData === undefined) {
                        return previousData;
                    }

                    return {
                        ...previousData,
                        pages: previousData.pages.map((page) => ({
                            ...page,
                            items: page.items.map((item) =>
                                item.id === data.media_id
                                    ? { ...item, subset: data.subset, user_reviewed: data.user_reviewed }
                                    : item
                            ),
                        })),
                    };
                }
            );

            if (isVideoFrame(mediaItem)) {
                incrementCachedAnnotatedFrameCount(queryClient, mediaItem);
            }
        },
    });
};

type UseSubmitAnnotationsParams = {
    mediaItem: Media;
    mode: AnnotatorMode;
};

export const useSubmitAnnotations = ({ mediaItem, mode }: UseSubmitAnnotationsParams) => {
    const projectId = useProjectIdentifier();
    const projectLabels = useProjectLabelsWithEmptyLabel();
    const { annotations, initialAnnotations, initialPredictions } = useAnnotations();
    const { resetAnnotations } = useAnnotationCommands();
    const saveMutation = useSaveAnnotationsMutation(mediaItem);

    const saveAnnotations = async (annotationsDTO: AnnotationDTO[], subset: DatasetSubset) => {
        const query = isVideoFrame(mediaItem) ? { frame_index: mediaItem.frame_number } : undefined;

        await saveMutation.mutateAsync({
            params: { path: { media_id: mediaItem.id, project_id: projectId }, query },
            body: { annotations: annotationsDTO, subset },
        });

        resetAnnotations(mapServerAnnotationsToLocal(annotationsDTO));
    };

    const submitAnnotations = async (subset: DatasetSubset) => {
        const validLabelIds = new Set(projectLabels.map((label) => label.id));
        const serverAnnotations = mapLocalAnnotationsToServer(
            filterOutAnnotationWithEmptyLabel(annotations),
            validLabelIds
        );

        await saveAnnotations(serverAnnotations, subset);
    };

    const submitPredictions = async (subset: DatasetSubset) => {
        const validLabelIds = new Set(projectLabels.map((label) => label.id));
        const serverPredictionsWithoutConfidences = mapLocalAnnotationsToServer(initialPredictions, validLabelIds)
            .map(({ confidences, ...restOfAnnotation }) => restOfAnnotation)
            .filter((annotation) => isNonEmptyArray(annotation.labels) && annotation.labels.every(isNonEmptyLabel));

        await saveAnnotations(serverPredictionsWithoutConfidences, subset);
    };

    const hasChangedAnnotations = useMemo(() => {
        const currentServerAnnotations = mapLocalAnnotationsToServer(filterOutAnnotationWithEmptyLabel(annotations));

        return !isEqual(currentServerAnnotations, mapLocalAnnotationsToServer(initialAnnotations));
    }, [annotations, initialAnnotations]);

    const hasEmptyLabelSelection = annotations.some((annotation) =>
        annotation.labels.some((label) => label.id === EMPTY_LABEL_ID)
    );
    const hasInvalidAnnotation = annotations.some((annotation) => annotation.labels.length === 0);

    const canSubmit =
        mode === 'prediction'
            ? initialPredictions.length > 0
            : !hasInvalidAnnotation && (hasChangedAnnotations || hasEmptyLabelSelection);

    return {
        canSubmit,
        hasInvalidAnnotation,
        isSaving: saveMutation.isPending,
        submitAnnotations,
        submitPredictions,
    };
};
