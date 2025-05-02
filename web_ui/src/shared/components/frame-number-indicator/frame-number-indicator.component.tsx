// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useNumberFormatter, View } from '@adobe/react-spectrum';

const useFormatFrames = (frames: number) => {
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
