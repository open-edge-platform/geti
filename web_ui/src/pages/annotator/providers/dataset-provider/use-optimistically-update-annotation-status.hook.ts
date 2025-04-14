// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteData, useQueryClient } from '@tanstack/react-query';
import isEqual from 'lodash/isEqual';
import isNumber from 'lodash/isNumber';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { AnnotationStatePerTask, MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import { MediaItem, MediaItemResponse } from '../../../../core/media/media.interface';
import { isVideoFrame } from '../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { SelectedMediaItem } from '../selected-media-item-provider/selected-media-item.interface';
import { useTask } from '../task-provider/task-provider.component';

interface UseOptimisticallyUpdateAnnotationStatus {
    (mediaItem: MediaItem, annotations: ReadonlyArray<Annotation>, annotationStates?: AnnotationStatePerTask[]): void;
}
export const useOptimisticallyUpdateAnnotationStatus = (
    datasetIdentifier: DatasetIdentifier
): UseOptimisticallyUpdateAnnotationStatus => {
    const queryClient = useQueryClient();

    const { selectedTask } = useTask();

    const mediaQueryKey = QUERY_KEYS.ADVANCED_MEDIA_ITEMS(datasetIdentifier, {}, {});
    const activeMediaQueryKey = QUERY_KEYS.ACTIVE_MEDIA_ITEMS(datasetIdentifier, null);

    const optimisticallyUpdateAnnotationStatus = (
        mediaItem: MediaItem,
        annotations: ReadonlyArray<Annotation>,
        annotationStates?: AnnotationStatePerTask[]
    ) => {
        const status = annotations.length > 0 ? MEDIA_ANNOTATION_STATUS.ANNOTATED : MEDIA_ANNOTATION_STATUS.NONE;

        // Updating the stored annotations makes it so that we can switch (and thus submit annotations) between
        // tasks without having to retrieve the annotations from the server again
        queryClient.setQueryData<ReadonlyArray<Annotation> | undefined>(
            QUERY_KEYS.SELECTED_MEDIA_ITEM.ANNOTATIONS(mediaItem.identifier),
            () => annotations
        );
        queryClient.setQueriesData<SelectedMediaItem | undefined>(
            { queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.SELECTED(mediaItem.identifier, selectedTask?.id) },
            (oldData) => {
                if (oldData === undefined) {
                    return undefined;
                }

                return { ...oldData, annotations: [...annotations] };
            }
        );

        // Remove the currently selected media item's query so that it uses the
        // new annotations as the currently saved annotations.
        // This disables saving the same annotations twice since we only allow
        // the user to submit annotations if they've made changes.
        queryClient.removeQueries({
            queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.SELECTED(mediaItem.identifier, selectedTask?.id),
        });

        // Fuzzy match (active) media query key to update the annotation status
        // of the selected media item
        const updateAnnotationStateOfMediaPages = (data: InfiniteData<MediaItemResponse> | undefined) => {
            if (data === undefined) {
                return data;
            }

            const pages = data.pages.map((page): MediaItemResponse => {
                const nextPage = page.nextPage;

                // Update status of mediaItem
                const media = page.media.map((cachedMediaItem) => {
                    if (isEqual(cachedMediaItem.identifier, mediaItem.identifier)) {
                        return { ...cachedMediaItem, status, annotationStatePerTask: annotationStates };
                    }

                    return cachedMediaItem;
                });

                return { nextPage, media, mediaCount: page.mediaCount };
            });

            return { ...data, pages };
        };

        queryClient.setQueriesData<InfiniteData<MediaItemResponse> | undefined>(
            { queryKey: mediaQueryKey },
            updateAnnotationStateOfMediaPages
        );
        queryClient.setQueriesData<InfiniteData<MediaItemResponse> | undefined>(
            { queryKey: activeMediaQueryKey },
            updateAnnotationStateOfMediaPages
        );

        // Optimistically update queries that fetch the label ids assigned to a video frame
        if (isVideoFrame(mediaItem)) {
            const timelineQueryKey = QUERY_KEYS.VIDEO_ANNOTATIONS(datasetIdentifier, {
                type: MEDIA_TYPE.VIDEO,
                videoId: mediaItem.identifier.videoId,
            });
            const frameNumber = mediaItem.identifier.frameNumber;

            queryClient.setQueriesData<Record<number, ReadonlyArray<Annotation>>>(
                {
                    predicate: (query) => {
                        const queryKey = query.queryKey;

                        if (!Array.isArray(queryKey) || queryKey.length < timelineQueryKey.length) {
                            return false;
                        }

                        // Check that the first part of the key is equal
                        // and options should include the mediaItem.identifier.frameNumber
                        const isVideoTimelineQueryKey = !timelineQueryKey.some((key, index) => {
                            // The last key of the timeline query is used for pagination options,
                            // we ignore these as we want to update all paginated data
                            const isNotLastKey = index !== timelineQueryKey.length - 1;

                            return !isEqual(key, query.queryKey[index]) && isNotLastKey;
                        });

                        if (!isVideoTimelineQueryKey) {
                            return false;
                        }

                        const options = queryKey[queryKey.length - 1];
                        if (!isNumber(options.startFrame) || !isNumber(options.endFrame)) {
                            return false;
                        }

                        if (options.startFrame <= frameNumber && options.endFrame >= frameNumber) {
                            return true;
                        }

                        return false;
                    },
                },
                (data) => {
                    if (data === undefined) {
                        data = {};
                    }

                    data[mediaItem.identifier.frameNumber] = annotations;

                    return data;
                }
            );
        }
    };

    return optimisticallyUpdateAnnotationStatus;
};
