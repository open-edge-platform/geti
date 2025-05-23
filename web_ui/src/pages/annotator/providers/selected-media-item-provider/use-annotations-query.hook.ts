// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { getErrorMessageByStatusCode } from '@geti/core/src/services/utils';
import { useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { AnnotationService } from '../../../../core/annotations/services/annotation-service.interface';
import { Label } from '../../../../core/labels/label.interface';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { isVideoFrame } from '../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { updateVideoTimelineQuery } from './utils';

interface UseGetAnnotations {
    annotationService: AnnotationService;
    coreLabels: Label[];
    datasetIdentifier: DatasetIdentifier;
    mediaItem: MediaItem | undefined;
    annotationId?: 'latest' | string;
    enabled?: boolean;
}

// We almost always want to receive the most recent annotations and not rely on a
// cache. The only exception is when using the video player, in that case we'd like
// to use the cache from propagating annotations and / or playing videos (where we
// prefetch images and annotations)
const CACHE_TIME = 100;

export const useAnnotationsQuery = ({
    annotationService,
    coreLabels,
    datasetIdentifier,
    mediaItem,
    annotationId = 'latest',
    enabled = true,
}: UseGetAnnotations): UseQueryResult<Annotation[], AxiosError> => {
    const queryClient = useQueryClient();
    const { addNotification } = useNotification();

    const isQueryEnabled = enabled && mediaItem !== undefined;

    const query = useQuery<Annotation[], AxiosError>({
        queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.ANNOTATIONS(mediaItem?.identifier, annotationId),
        queryFn: async () => {
            if (mediaItem === undefined) {
                throw new Error("Can't fetch undefined media item");
            }

            return annotationService.getAnnotations(datasetIdentifier, coreLabels, mediaItem, annotationId);
        },
        enabled: isQueryEnabled,
        gcTime: CACHE_TIME,
    });

    useEffect(() => {
        if (!isQueryEnabled || !query.isSuccess) {
            return;
        }

        const annotations = query.data;

        if (mediaItem !== undefined && isVideoFrame(mediaItem)) {
            const videoTimelineQueryKeyPrefix = QUERY_KEYS.VIDEO_ANNOTATIONS(datasetIdentifier, {
                type: MEDIA_TYPE.VIDEO,
                videoId: mediaItem.identifier.videoId,
            });

            updateVideoTimelineQuery(queryClient, videoTimelineQueryKeyPrefix, mediaItem, annotations);
        }
    }, [isQueryEnabled, query.isSuccess, query.data, mediaItem, datasetIdentifier, queryClient]);

    useEffect(() => {
        if (!query.isError) {
            return;
        }

        const message = getErrorMessageByStatusCode(query.error);
        addNotification({ message: `${message} when getting annotations`, type: NOTIFICATION_TYPE.ERROR });
    }, [query.isError, query.error, addNotification]);

    return query;
};
