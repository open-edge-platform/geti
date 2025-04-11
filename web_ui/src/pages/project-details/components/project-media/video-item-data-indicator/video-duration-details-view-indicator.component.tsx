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

import { useDurationText } from '../../../../../shared/hooks/data-format/use-duration-text.hook';
import { VideoItemDataIndicator } from './video-item-data-indicator.component';

interface VideoDurationDetailsVideIndicatorProps {
    duration: number;
    tooltip: string;
}
export const VideoDurationDetailsViewIndicator = ({
    duration,
    tooltip,
}: VideoDurationDetailsVideIndicatorProps): JSX.Element => {
    const durationText = useDurationText(duration);

    return (
        <VideoItemDataIndicator tooltip={tooltip} id={'video-indicator-duration-id'}>
            {durationText}
        </VideoItemDataIndicator>
    );
};
