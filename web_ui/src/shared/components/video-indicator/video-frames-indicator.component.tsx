// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
