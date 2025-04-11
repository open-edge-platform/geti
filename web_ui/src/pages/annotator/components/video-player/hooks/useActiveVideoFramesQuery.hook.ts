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
