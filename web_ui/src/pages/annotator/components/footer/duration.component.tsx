// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import { useDurationText } from '@shared/hooks/data-format/use-duration-text.hook';

import { TimeSmall } from '../../../../assets/icons';
import { isVideoFrame, Video, VideoFrame } from '../../../../core/media/video.interface';

export const Duration = ({
    mediaItem,
    className,
    isLargeSize,
}: {
    mediaItem: Video | VideoFrame;
    className?: string;
    isLargeSize: boolean;
}): JSX.Element => {
    const endTime = mediaItem.metadata.duration;
    const paddingX = isLargeSize ? 'size-200' : 'size-100';
    const currentTime = isVideoFrame(mediaItem) ? mediaItem.identifier.frameNumber / mediaItem.metadata.fps : 0;

    const currentTimeText = useDurationText(currentTime);
    const endTimeText = useDurationText(endTime);

    if (isNaN(currentTime) || endTime === undefined) {
        return <></>;
    }

    return (
        <View height='100%' paddingX={paddingX} UNSAFE_className={className}>
            {isLargeSize && <TimeSmall />}
            <span style={{ fontSize: dimensionValue('size-130') }} id='video-duration' aria-label='duration'>
                {currentTimeText} / {endTimeText}
            </span>
        </View>
    );
};
