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

import { useNumberFormatter, View } from '@adobe/react-spectrum';

export const useFormatFrames = (frames: number) => {
    const formatter = useNumberFormatter({
        minimumFractionDigits: 0,
        maximumFractionDigits: 1,
        notation: 'compact',
    });

    return formatter.format(frames);
};

interface FrameNumberIndicatorProps {
    frameNumber: number;
}

export const FrameNumberIndicator = ({ frameNumber }: FrameNumberIndicatorProps): JSX.Element => {
    const formattedFrames = useFormatFrames(frameNumber);

    return (
        <View
            position='absolute'
            backgroundColor='gray-50'
            right={4}
            top={4}
            borderRadius={'regular'}
            paddingX='size-75'
            paddingY='size-25'
            UNSAFE_style={{ color: 'white', fontSize: '12px' }}
        >
            {formattedFrames}f
        </View>
    );
};
