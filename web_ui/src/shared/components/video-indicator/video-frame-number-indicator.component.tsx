// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
