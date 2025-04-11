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
import isEmpty from 'lodash/isEmpty';

import { useDurationText } from '../../../../../shared/hooks/data-format/use-duration-text.hook';
import { useFramesText } from '../../../../../shared/hooks/data-format/use-frames-text.hook';

interface DatasetListItemVideoDetailsProps {
    className: string;
    frames: number | undefined;
    duration: number;
}
export const DatasetListItemVideoDetails = ({
    className,
    frames,
    duration,
}: DatasetListItemVideoDetailsProps): JSX.Element => {
    const framesText = useFramesText(frames);
    const durationText = useDurationText(duration);

    return (
        <View width={'inherit'} UNSAFE_className={className}>
            <>{isEmpty(framesText) ? durationText : `${framesText} --- ${durationText}`}</>
        </View>
    );
};
