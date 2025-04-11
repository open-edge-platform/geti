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

import { useDurationText } from '../../hooks/data-format/use-duration-text.hook';
import { IndicatorWrapper } from '../indicator-wrapper/indicator-wrapper.component';
import { VideoFramesIndicator } from './video-frames-indicator.component';

import classes from './video-indicator.module.scss';

interface VideoIndicatorProps {
    duration: number;
    frames: number | undefined;
}

export const VideoIndicator = ({ duration, frames }: VideoIndicatorProps): JSX.Element => {
    const shouldShowFramesIndicator = frames !== undefined;
    const durationText = useDurationText(duration);

    return (
        <>
            {shouldShowFramesIndicator && <VideoFramesIndicator frames={frames} />}
            <IndicatorWrapper
                id={'video-indicator-duration-id'}
                data-testid={'video-indicator-duration-id'}
                left={'size-50'}
                bottom={'size-50'}
                UNSAFE_className={classes.videoFrameText}
            >
                {durationText}
            </IndicatorWrapper>
        </>
    );
};
