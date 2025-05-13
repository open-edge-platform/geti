// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { noop } from 'lodash-es';

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
