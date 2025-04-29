// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useQuery } from '@tanstack/react-query';
import isNil from 'lodash/isNil';
import sortBy from 'lodash/sortBy';

import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';
import { useDataset } from '../../../providers/dataset-provider/dataset-provider.component';

export const useActiveVideoFramesQuery = (videoFrame: MediaItem | undefined) => {
    const { activeMediaItemsQuery } = useDataset();

    const activeMediaItemsData = activeMediaItemsQuery.data;
    const enabled = videoFrame !== undefined && isVideoFrame(videoFrame);

    return useQuery({
        queryKey: ['active-video-frames', enabled ? videoFrame.identifier.videoId : null],
        queryFn: () => {
            if (!enabled) {
                return [];
            }

            if (activeMediaItemsData === undefined || isNil(activeMediaItemsData.pages)) {
                return [];
            }

            const activeVideoFrames = activeMediaItemsData.pages
                .flatMap((page) => page.media)
                .filter((mediaItem): mediaItem is VideoFrame => {
                    if (!isVideoFrame(mediaItem)) {
                        return false;
                    }

                    return mediaItem.identifier.videoId === videoFrame.identifier.videoId;
                });

            return sortBy(activeVideoFrames, ({ identifier: { frameNumber } }) => frameNumber).map(
                ({ identifier }) => identifier.frameNumber
            );
        },
        enabled: enabled && activeMediaItemsData !== undefined,
        initialData: [],
    });
};
