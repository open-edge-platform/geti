// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RefObject, useRef } from 'react';

import { useNumberFormatter, View, VisuallyHidden } from '@adobe/react-spectrum';
import { isArray } from 'lodash-es';
import { mergeProps, useFocusRing, useSlider, useSliderThumb } from 'react-aria';
import { SliderState, useSliderState } from 'react-stately';

import { VideoThumb } from '../../../../../assets/icons';
import { VideoFrame } from '../../../../../core/media/video.interface';

import classes from './video-player.module.scss';

interface ThumbProps {
    state: SliderState;
    index: number;
    trackRef: RefObject<HTMLDivElement>;
}
const Thumb = ({ state, trackRef, index }: ThumbProps) => {
    const inputRef = useRef(null);
    const { thumbProps, inputProps } = useSliderThumb({ index, trackRef, inputRef }, state);

    const { focusProps } = useFocusRing();
    return (
        <div
            className={classes.timelineThumb}
            style={{ left: `${state.getThumbPercent(index) * 100}%` }}
            aria-label={'Video thumb'}
            {...thumbProps}
        >
            <VideoThumb />
            <VisuallyHidden>
                <input ref={inputRef} {...mergeProps(inputProps, focusProps)} />
            </VisuallyHidden>
        </div>
    );
};

interface SliderProps {
    sliderValue: number;
    onSliderValueChange: (value: number) => void;
    onSliderValueChangeEnd: (value: number) => void;
    videoFrame: VideoFrame;
}

// This component mimicks Adobe Spectrum's slider, but uses react-aria's useSlider props so that
// we have more control over its styling
// @see https://react-spectrum.adobe.com/react-aria/useSlider.html#single-thumb
export const VideoTimelineSlider = ({
    sliderValue,
    onSliderValueChange,
    videoFrame,
    onSliderValueChangeEnd,
}: SliderProps) => {
    const numberFormatter = useNumberFormatter({});

    const props = {
        minValue: 0,
        maxValue: videoFrame.metadata.frames - 1,
        step: 1,
        value: [sliderValue],
        defaultValue: [videoFrame.identifier.frameNumber],
        onChange: (values: number | number[]) => {
            if (isArray(values)) {
                onSliderValueChange(values[0]);
            } else {
                onSliderValueChange(values);
            }
        },
        onChangeEnd: (frameNumber: number | number[]) => {
            if (isArray(frameNumber)) {
                onSliderValueChangeEnd(frameNumber[0]);
            } else {
                onSliderValueChangeEnd(frameNumber);
            }
        },
        numberFormatter,
        'aria-label': 'Seek in video',
        'aria-valuetext': `Video is at frame ${videoFrame.identifier.frameNumber} of ${videoFrame.metadata.frames}`,
    };
    const state = useSliderState(props);

    const trackRef = useRef<HTMLDivElement>(null);
    const { groupProps, trackProps } = useSlider(props, state, trackRef);

    return (
        <div {...groupProps} className={classes.timelineGroup} data-testid={'video-timeline-slider-id'}>
            <div {...trackProps} ref={trackRef} className={classes.timelineTrackGroup}>
                {/* The track is separated by one filled (white) line and unfilled line */}
                <View UNSAFE_className={classes.timelineTrack} width={`${state.getThumbPercent(0) * 100}%`} />
                <View
                    UNSAFE_className={classes.timelineTrack}
                    width={`${100 - state.getThumbPercent(0) * 100}%`}
                    left={`calc(${state.getThumbPercent(0) * 100}%`}
                    backgroundColor={'gray-400'}
                />
                <Thumb index={0} state={state} trackRef={trackRef} />
            </div>
        </div>
    );
};
