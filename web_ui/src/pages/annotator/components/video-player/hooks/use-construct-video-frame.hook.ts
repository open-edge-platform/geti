// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback } from 'react';

import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { MEDIA_ANNOTATION_STATUS } from '../../../../../core/media/base.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideo, isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';
import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';

export const useConstructVideoFrame = (videoFrame: MediaItem | undefined) => {
    const datasetIdentifier = useDatasetIdentifier();

    const { router } = useApplicationServices();
    return useCallback(
        (frameNumber: number | undefined, frames?: VideoFrame[]): VideoFrame | undefined => {
            if (videoFrame === undefined || (!isVideoFrame(videoFrame) && !isVideo(videoFrame))) {
                return;
            }

            if (frameNumber === undefined || frameNumber > videoFrame.metadata.frames) {
                return;
            }

            const {
                metadata,
                name,
                uploadTime,
                uploaderId,
                identifier: { videoId },
                lastAnnotatorId,
            } = videoFrame;

            const identifier = {
                type: MEDIA_TYPE.VIDEO_FRAME,
                videoId,
                frameNumber,
            } as const;

            const src = router.MEDIA_ITEM_SRC(datasetIdentifier, identifier);
            const thumbnailSrc = router.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, identifier);

            // We're assuming that the video is not annotated nor analysed as this
            // is not important for the videoplayer
            const status = MEDIA_ANNOTATION_STATUS.NONE;

            const frame = frames?.find((item) => item.identifier.frameNumber === frameNumber);

            if (frame) {
                return {
                    ...frame,
                    metadata,
                    src,
                    thumbnailSrc,
                    status,
                    identifier,
                    name,
                };
            }

            return {
                identifier,
                src,
                thumbnailSrc,
                status,
                name,
                metadata,
                annotationStatePerTask: [],
                uploadTime,
                uploaderId,
                lastAnnotatorId,
            };
        },
        [datasetIdentifier, videoFrame, router]
    );
};
