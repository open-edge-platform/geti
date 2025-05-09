// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { maxBy } from 'lodash-es';

import { Annotation, TaskChainInput } from '../../../core/annotations/annotation.interface';
import { isVideo } from '../../../core/media/video.interface';
import { FindMediaItemCriteria, FindVideoFrameCriteria } from '../hooks/use-next-media-item.hook';
import { findIndex } from '../utils';

export const findNextCriteria: FindMediaItemCriteria = (selectedMediaItem, mediaItems) => {
    const idx = findIndex(selectedMediaItem, mediaItems);

    if (idx + 1 < mediaItems.length) {
        return { type: 'media', media: mediaItems[idx + 1] };
    }

    return undefined;
};

export const findNextVideoFrameCriteria: FindVideoFrameCriteria = (selectedMediaItem, videoFrames) => {
    if (isVideo(selectedMediaItem)) {
        return { type: 'videoFrame', frameNumber: videoFrames[0] };
    }

    const selectedVideoFrameIndex = videoFrames.findIndex(
        (frameNumber) => frameNumber === selectedMediaItem.identifier.frameNumber
    );

    if (selectedVideoFrameIndex !== -1 && selectedVideoFrameIndex < videoFrames.length) {
        const nextFrameNumber = videoFrames[selectedVideoFrameIndex + 1];
        if (nextFrameNumber) {
            return { type: 'videoFrame', frameNumber: nextFrameNumber };
        }
    }

    const nextFrameNumber = videoFrames.find((frameNumber) => {
        return frameNumber > selectedMediaItem.identifier.frameNumber;
    });

    if (nextFrameNumber) {
        return { type: 'videoFrame', frameNumber: nextFrameNumber };
    }
    return undefined;
};

export const FRAME_STEP_TO_DISPLAY_ALL_FRAMES = 1;

export const findNextAnnotationCriteria = (selectedInput: Annotation | undefined, inputs: TaskChainInput[]) => {
    const inputsAfterSelectedInput = inputs.filter(({ id, zIndex }) => {
        if (selectedInput === undefined) {
            return true;
        }

        return id !== selectedInput.id && selectedInput.zIndex > zIndex;
    });

    return maxBy(inputsAfterSelectedInput, ({ zIndex }) => zIndex);
};

export const formatPerformanceScore = (score: number | null): string => {
    const formattedScore = score !== null ? `${Math.round(score * 100)}%` : 'N/A';

    return formattedScore;
};
