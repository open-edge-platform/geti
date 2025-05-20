// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text } from '@geti/ui';

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
