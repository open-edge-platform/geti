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

import { useFramesText } from '../../hooks/data-format/use-frames-text.hook';
import { IndicatorWrapper } from '../indicator-wrapper/indicator-wrapper.component';

import classes from './video-indicator.module.scss';

export const VideoFramesIndicator = ({ frames }: { frames: number }): JSX.Element => {
    const frameText = useFramesText(frames);

    return (
        <IndicatorWrapper
            id={'video-indicator-frames-id'}
            data-testid={'video-indicator-frames-id'}
            right={'size-50'}
            top={'size-50'}
            UNSAFE_className={classes.videoFrameText}
        >
            {frameText}
        </IndicatorWrapper>
    );
};
