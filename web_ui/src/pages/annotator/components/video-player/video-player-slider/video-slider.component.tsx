// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ElementRef, MutableRefObject, useRef } from 'react';

import { SpectrumSliderProps, useNumberFormatter, VisuallyHidden } from '@geti/ui';
import { AriaSliderProps, mergeProps, useFocusRing, useSlider, useSliderThumb } from 'react-aria';
import { SliderState, useSliderState } from 'react-stately';

import classes from './video-player-slider.module.scss';

interface ThumbProps {
    index: number;
    state: SliderState;
    trackWidth: string;
    trackRef: MutableRefObject<HTMLDivElement | null>;
}

interface BufferRange {
    startFrame: number;
    endFrame: number;
    status: 'loading' | 'success';
}

interface VideoSliderProps extends SpectrumSliderProps {
    leftOffset?: number;
    sizePerSquare?: number;
    highlightedFrames: number[];
    highlightedFramesColor?: string;
    buffers?: BufferRange[];
    lastFrame: number;
}

const getPositionOfThumbForLastFrame = (trackRef: HTMLDivElement | null, leftOffset: number): string => {
    if (trackRef === null) {
        return '0px';
    }

    const THUMB_OFFSET = 8;

    return `${trackRef.getBoundingClientRect().width - THUMB_OFFSET - leftOffset}px`;
};

const THUMB_INDEX = 0;

export const VideoSlider = ({
    leftOffset = 0,
    sizePerSquare,
    highlightedFrames,
    highlightedFramesColor = 'var(--brand-daisy)',
    buffers = [],
    lastFrame,
    ...props
}: VideoSliderProps) => {
    const trackRef = useRef<ElementRef<'div'>>(null);
    const sliderProps = props as unknown as AriaSliderProps<number | number[]>;

    const numberFormatter = useNumberFormatter(props.formatOptions);
    const state = useSliderState({ ...props, numberFormatter });
    const { groupProps, trackProps } = useSlider(sliderProps, state, trackRef);
    const [value] = state.values;
    const isLastFrame = value >= lastFrame;

    const trackWidth = isLastFrame
        ? getPositionOfThumbForLastFrame(trackRef.current, leftOffset)
        : sizePerSquare
          ? `${sizePerSquare * (value / state.step)}px`
          : `${state.getThumbPercent(THUMB_INDEX) * 100}%`;

    return (
        <div
            {...groupProps}
            className={classes.slider}
            style={{
                overflow: leftOffset === 0 || value === props.minValue ? 'visible' : 'hidden',
            }}
        >
            <div
                {...trackProps}
                ref={trackRef}
                style={{ left: `${leftOffset}px` }}
                className={`${classes.track} ${state.isDisabled ? classes.disabled : ''}`}
            >
                {buffers.map(({ startFrame, endFrame, status }, idx) => {
                    const isLoading = status === 'loading';

                    return (
                        <div
                            key={`${startFrame}-${endFrame}-${idx}`}
                            aria-label={
                                isLoading
                                    ? `Loading predictions for frames ${startFrame} to ${endFrame}`
                                    : `Finished loading predictions for frames ${startFrame} to ${endFrame}`
                            }
                            className={
                                isLoading
                                    ? [classes.bufferTrack, classes.loadingBufferTrack, classes.loadingGradient].join(
                                          ' '
                                      )
                                    : classes.bufferTrack
                            }
                            style={{
                                left: `${state.getValuePercent(startFrame) * 100}%`,
                                width: `${
                                    (state.getValuePercent(endFrame) - state.getValuePercent(startFrame)) * 100
                                }%`,
                            }}
                        ></div>
                    );
                })}

                <div className={classes.lowerTrack} style={{ width: trackWidth }}></div>

                {highlightedFrames.map((frame) => (
                    <div
                        key={`highlight-${frame}`}
                        className={classes.highlightPosition}
                        aria-label={`highlight-frame-${frame}`}
                        style={{ left: `${state.getValuePercent(frame) * 100}%`, background: highlightedFramesColor }}
                    ></div>
                ))}

                <Thumb index={THUMB_INDEX} state={state} trackRef={trackRef} trackWidth={trackWidth} />
            </div>
        </div>
    );
};

const Thumb = ({ state, trackRef, index, trackWidth }: ThumbProps) => {
    const inputRef = useRef(null);
    const { focusProps } = useFocusRing();
    const { thumbProps, inputProps } = useSliderThumb(
        {
            index,
            trackRef,
            inputRef,
        },
        state
    );

    return (
        <div {...thumbProps} style={{ ...thumbProps.style, left: trackWidth }} className={classes.thumb}>
            <VisuallyHidden>
                <input ref={inputRef} {...mergeProps(inputProps, focusProps)} />
            </VisuallyHidden>
        </div>
    );
};
