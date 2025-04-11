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

import { useMemo } from 'react';

import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import range from 'lodash/range';
import sortBy from 'lodash/sortBy';

import { Annotation, TaskChainInput } from '../../../core/annotations/annotation.interface';
import { MediaItem } from '../../../core/media/media.interface';
import { isVideo, isVideoFrame, Video, VideoFrame } from '../../../core/media/video.interface';
import { useFilteredVideoFramesQuery } from '../components/video-player/hooks/use-filtered-video-frames-query.hook';
import { useActiveVideoFramesQuery } from '../components/video-player/hooks/useActiveVideoFramesQuery.hook';
import { useVideoPlayerContext } from '../components/video-player/video-player-provider.component';
import { useDataset } from '../providers/dataset-provider/dataset-provider.component';
import { useTaskChain } from '../providers/task-chain-provider/task-chain-provider.component';

type FindMediaItemCriteriaOutput =
    | { type: 'annotation'; annotation: Annotation }
    | { type: 'videoFrame'; frameNumber: number }
    | { type: 'media'; media: MediaItem }
    | undefined;

export interface FindMediaItemCriteria {
    (selectedMediaItem: MediaItem | undefined, mediaItems: MediaItem[]): FindMediaItemCriteriaOutput;
}

export interface FindVideoFrameCriteria {
    (selectedMediaItem: VideoFrame | Video, videoFrames: number[]): FindMediaItemCriteriaOutput;
}

interface FindAnnotationCriteria {
    (selectedInput: Annotation | undefined, inputAnnotations: TaskChainInput[]): undefined | Annotation;
}

const useMediaItems = (): MediaItem[] => {
    const { mediaItemsQuery } = useDataset();
    const mediaItemsData = mediaItemsQuery.data;

    return useMemo(() => {
        return mediaItemsData?.pages?.flatMap(({ media }) => media) ?? [];
    }, [mediaItemsData]);
};

const findNextMediaItemBasedOnVideoFrames = (
    selectedMediaItem: VideoFrame | Video,
    videoFrames: number[],
    mediaItems: MediaItem[],
    findCriteria: FindMediaItemCriteria,
    findVideoCriteria: FindVideoFrameCriteria
) => {
    const nextVideo = findVideoCriteria(selectedMediaItem, videoFrames);

    if (nextVideo !== undefined) {
        return nextVideo;
    }

    const mediaItemsWithoutSelectedVideo = mediaItems.filter((mediaItem) => {
        // Only include the selected video frame
        if (isVideoFrame(mediaItem)) {
            return (
                mediaItem.identifier.videoId !== selectedMediaItem.identifier.videoId ||
                isEqual(mediaItem.identifier, selectedMediaItem.identifier)
            );
        }

        return true;
    });

    return findCriteria(selectedMediaItem, mediaItemsWithoutSelectedVideo);
};

export const useNextMediaItem = (
    selectedMediaItem: MediaItem | undefined,
    findCriteria: FindMediaItemCriteria,
    findVideoCriteria?: FindVideoFrameCriteria,
    findAnnotationCriteria?: FindAnnotationCriteria
): ReturnType<FindMediaItemCriteria> => {
    const mediaItems = useMediaItems();
    const { inputs } = useTaskChain();

    const inputsWithOutputs = useMemo(() => {
        return sortBy(inputs, ({ zIndex }) => zIndex);
    }, [inputs]);

    const annotation = useMemo(() => {
        // Try to find annotation
        if (inputsWithOutputs.length > 0 && findAnnotationCriteria !== undefined) {
            return findAnnotationCriteria(
                inputsWithOutputs.find(({ isSelected }) => isSelected),
                inputsWithOutputs
            );
        }

        return undefined;
    }, [findAnnotationCriteria, inputsWithOutputs]);

    const videoContext = useVideoPlayerContext();
    const { data: filteredFrames } = useFilteredVideoFramesQuery(selectedMediaItem);
    const { data: activeVideoFrames } = useActiveVideoFramesQuery(selectedMediaItem);
    const { isInActiveMode } = useDataset();

    const videoFrames = useMemo(() => {
        if (videoContext === undefined) {
            return [];
        }

        if (isInActiveMode) {
            return activeVideoFrames ?? [];
        }

        return isEmpty(filteredFrames)
            ? range(0, videoContext.videoFrame?.metadata?.frames, videoContext.step)
            : filteredFrames;
    }, [videoContext, activeVideoFrames, filteredFrames, isInActiveMode]);

    // TODO: separate into two useMemo's so that we don't recalculate the media item when
    // annotations change
    return useMemo(() => {
        // Try to find annotation
        if (annotation !== undefined) {
            return { type: 'annotation' as const, annotation };
        }
        // Try to find a next media item in video frames
        if (
            findVideoCriteria !== undefined &&
            selectedMediaItem !== undefined &&
            (isVideo(selectedMediaItem) || isVideoFrame(selectedMediaItem))
        ) {
            return findNextMediaItemBasedOnVideoFrames(
                selectedMediaItem,
                videoFrames,
                mediaItems,
                findCriteria,
                findVideoCriteria
            );
        }

        return findCriteria(selectedMediaItem, mediaItems);
    }, [annotation, findVideoCriteria, selectedMediaItem, findCriteria, mediaItems, videoFrames]);
};
