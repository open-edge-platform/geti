// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import noop from 'lodash/noop';

import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideoFrame } from '../../../../../core/media/video.interface';
import { TestMediaItem } from '../../../../../core/tests/test-media.interface';
import { useConstructVideoFrame } from '../../../../annotator/components/video-player/hooks/use-construct-video-frame.hook';
import { VideoControls } from '../../../../annotator/components/video-player/video-controls/video-controls.interface';

export const useVideoControls = ({
    testMediaItem,
    setSelectedMediaItem,
    selectedMediaItem,
}: {
    testMediaItem: TestMediaItem;
    setSelectedMediaItem: (m: MediaItem) => void;
    selectedMediaItem: MediaItem;
}) => {
    const construct = useConstructVideoFrame(testMediaItem.media);

    if (!(testMediaItem.type === 'video' && isVideoFrame(selectedMediaItem))) {
        return;
    }

    const idx = testMediaItem.filteredFrames.findIndex((result) => {
        return selectedMediaItem.identifier.frameNumber === result.frameIndex;
    });

    const canSelectNext = idx < testMediaItem.filteredFrames.length - 1;
    const canSelectPrevious = idx > 0;

    const goto = (frameNumber: number) => {
        const videoFrame = construct(frameNumber);

        if (videoFrame) {
            setSelectedMediaItem(videoFrame);
        }
    };

    const videoControls: VideoControls = {
        canSelectNext,
        canSelectPrevious,
        goto,
        isPlaying: false,
        next: () => {
            if (canSelectNext) {
                goto(testMediaItem.filteredFrames[idx + 1].frameIndex);
            }
        },
        previous: () => {
            if (canSelectPrevious) {
                goto(testMediaItem.filteredFrames[idx - 1].frameIndex);
            }
        },
        pause: noop,
        play: noop,
    };

    return videoControls;
};
