// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
