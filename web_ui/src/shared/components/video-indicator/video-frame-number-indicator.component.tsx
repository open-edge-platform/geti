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

import { IndicatorWrapper } from '../indicator-wrapper/indicator-wrapper.component';

import classes from './video-indicator.module.scss';

interface VideoFrameIndicatorProps {
    frameNumber: number;
}

export const VideoFrameNumberIndicator = ({ frameNumber }: VideoFrameIndicatorProps): JSX.Element => {
    return (
        <IndicatorWrapper
            id={'video-frame-indicator-id'}
            data-testid={'video-frame-indicator-id'}
            top={'size-50'}
            right={'size-50'}
            UNSAFE_className={classes.videoFrameText}
        >
            {frameNumber}F
        </IndicatorWrapper>
    );
};
