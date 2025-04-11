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

import { View } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';

import { TimeSmall } from '../../../../assets/icons';
import { isVideoFrame, Video, VideoFrame } from '../../../../core/media/video.interface';
import { useDurationText } from '../../../../shared/hooks/data-format/use-duration-text.hook';

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
