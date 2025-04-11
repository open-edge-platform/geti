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

import { useNumberFormatter, View } from '@adobe/react-spectrum';
import { dimensionValue, useMediaQuery } from '@react-spectrum/utils';

import { Fps } from '../../../../assets/icons';
import { Video, VideoFrame } from '../../../../core/media/video.interface';
import { biggerThanQuery } from '../../../../theme/queries';

export const FPS = ({ mediaItem, className }: { mediaItem: Video | VideoFrame; className?: string }): JSX.Element => {
    const formatter = useNumberFormatter({
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    const isBiggerThan1020px = useMediaQuery(biggerThanQuery('1020'));

    if (isNaN(mediaItem.metadata.fps)) {
        return <></>;
    }

    return (
        <View height='100%' paddingX={'size-100'} UNSAFE_className={className}>
            {isBiggerThan1020px && <Fps />}
            <span style={{ fontSize: dimensionValue('size-130') }} id='video-fps' aria-label='fps'>
                {formatter.format(mediaItem.metadata.fps)} fps
            </span>
        </View>
    );
};
