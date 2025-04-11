// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo, useState } from 'react';

import { QueryClient, QueryKey } from '@tanstack/react-query';
import isArray from 'lodash/isArray';
import isEqual from 'lodash/isEqual';
import isNumber from 'lodash/isNumber';
import { useParams } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { roiFromImage } from '../../../../core/annotations/math';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { MediaIdentifier, MediaItem } from '../../../../core/media/media.interface';
import { isVideo, VideoFrame } from '../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { API_URLS } from '../../../../core/services/urls';
import { SelectedMediaItem } from './selected-media-item.interface';
import { useMediaItemQuery } from './use-media-item-query.hook';

export const getPendingMediaItem = (
    datasetIdentifier: DatasetIdentifier,
    pendingMediaItem: MediaItem | undefined,
    router: typeof API_URLS
): MediaItem | undefined => {
    if (!pendingMediaItem) {
        return undefined;
    }

    if (isVideo(pendingMediaItem)) {
        // If the user selected a video then we want to load its first frame by default
        const identifier = {
            type: MEDIA_TYPE.VIDEO_FRAME,
            videoId: pendingMediaItem.identifier.videoId,
            frameNumber: 0,
        } as const;
        const src = router.MEDIA_ITEM_SRC(datasetIdentifier, identifier);
        const thumbnailSrc = router.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, identifier);

        return {
            ...pendingMediaItem,
            identifier,
            src,
            thumbnailSrc,
        };
    }

    return pendingMediaItem;
};

export const constructClassificationAnnotations = (selectedMediaItem: SelectedMediaItem): Annotation[] => {
    if (selectedMediaItem.annotations.length > 0) {
        return selectedMediaItem.annotations.map((annotation) => {
            return { ...annotation, isSelected: true };
        });
    }

    const roi = roiFromImage(selectedMediaItem.image);

    // Construct a new annotation that is selected so that label keybindings will change this
    // annotation's labels
    return [
        {
            id: uuidv4(),
            shape: { shapeType: ShapeType.Rect, ...roi },
            labels: [],
            zIndex: 0,
            isSelected: true,
            isHidden: false,
            isLocked: false,
        },
    ];
};

export const useMediaIdentifierFromRoute = (): MediaIdentifier | undefined => {
    const params = useParams<{ imageId?: string; videoId?: string; frameNumber?: string }>();

    return useMemo(() => {
        const { imageId, videoId, frameNumber } = params;

        if (imageId !== undefined) {
            return {
                type: MEDIA_TYPE.IMAGE,
                imageId,
            };
        }

        if (videoId !== undefined) {
            if (frameNumber !== undefined) {
                return {
                    type: MEDIA_TYPE.VIDEO_FRAME,
                    videoId,
                    frameNumber: Number(frameNumber),
                };
            }

            return {
                type: MEDIA_TYPE.VIDEO,
                videoId,
            };
        }

        return undefined;
    }, [params]);
};

export const usePendingMediaItem = (datasetIdentifier: DatasetIdentifier, selectedMediaItem: MediaItem | undefined) => {
    const [pendingMediaItem, setPendingMediaItemState] = useState<MediaItem | undefined>(undefined);
    const mediaIdentifier = useMediaIdentifierFromRoute();

    useMediaItemQuery(
        datasetIdentifier,
        mediaIdentifier,
        {
            // Load the pending media item if the current route is not representative
            // of the pending or currently selected media item
            enabled:
                mediaIdentifier !== undefined &&
                !isEqual(mediaIdentifier, selectedMediaItem?.identifier) &&
                !isEqual(mediaIdentifier, pendingMediaItem?.identifier),
        },
        setPendingMediaItem
    );

    function setPendingMediaItem(mediaItem: MediaItem | undefined) {
        // This is a potential fix to the issue where we're loading the first media
        // item of the current dataset while the user has opened the annotator with a
        // specific media item url
        if (mediaItem !== undefined && mediaIdentifier !== undefined && pendingMediaItem === undefined) {
            // Do allow selecting the pending media item from the annotator route
            if (!isEqual(mediaIdentifier, mediaItem.identifier)) {
                return;
            }
        }

        setPendingMediaItemState(mediaItem);
    }

    return [pendingMediaItem, setPendingMediaItem] as const;
};

export const updateVideoTimelineQuery = (
    queryClient: QueryClient,
    timelineQueryKey: QueryKey,
    mediaItem: VideoFrame,
    annotations: ReadonlyArray<Annotation>
) => {
    if (!isArray(timelineQueryKey)) {
        return;
    }

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
                return {};
            }

            data[mediaItem.identifier.frameNumber] = annotations;

            return data;
        }
    );
};
