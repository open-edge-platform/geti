// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue, View } from '@geti/ui';

import { VideoFrame } from '../../../../core/media/video.interface';

interface FrameNumberProps {
    mediaItem: VideoFrame;
    className?: string;
}

export const FrameNumber = ({ mediaItem, className }: FrameNumberProps): JSX.Element => {
    return (
        <View height='100%' UNSAFE_className={className} paddingX={'size-100'}>
            <span style={{ fontSize: dimensionValue('size-130') }} id='frame-number' aria-label='frame number'>
                {`${mediaItem.identifier.frameNumber}F`}
            </span>
        </View>
    );
};
