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

import { Text } from '@adobe/react-spectrum';

import classes from './video-frames.module.scss';

interface VideoFramesProps {
    currentFrameNumber: number;
    totalFramesNumber: number;
}

export const VideoFrames = ({ currentFrameNumber, totalFramesNumber }: VideoFramesProps): JSX.Element => {
    return (
        <Text UNSAFE_className={classes.videoFrameText}>
            <span id='video-current-frame-number' aria-label='Currently selected frame number'>
                current frame {currentFrameNumber}
            </span>{' '}
            /{' '}
            <span aria-label='Total frames' id={'video-total-frames'}>
                total frames{' '}
                <span aria-label={'Total frames number'} id={'video-total-frames-number'}>
                    {totalFramesNumber}
                </span>
            </span>
        </Text>
    );
};
