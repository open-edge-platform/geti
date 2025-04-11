// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
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
