// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RefObject, useRef } from 'react';

import { useNumberFormatter, VisuallyHidden } from '@geti/ui';
import { mergeProps, useFocusRing, useSlider, useSliderThumb } from 'react-aria';
import { SliderState, useSliderState } from 'react-stately';

import { EndRangeVideoThumb, StartRageVideoThumb } from '../../../../../assets/icons';
import { Label } from '../../../../../core/labels/label.interface';
import { RangeSection } from './range-section.component';

import classes from './video-player.module.scss';

interface ResizeRangeThumbProps {
    isActive: boolean;
    index: number;
    trackRef: RefObject<HTMLDivElement>;
    state: SliderState;
    showResizeIcons: boolean;
}

const ThumbIndicator = ({ left }: { left: string }) => {
    return <div className={classes.thumbIndicator} style={{ left }} />;
};

const ResizeRangeThumb = ({ isActive, index, state, trackRef, showResizeIcons }: ResizeRangeThumbProps) => {
    const inputRef = useRef(null);
    const { thumbProps, inputProps } = useSliderThumb(
        { index, trackRef, inputRef, 'aria-label': index === 0 ? 'Minimum' : 'Maximum' },
        state
    );
    const { focusProps, isFocusVisible } = useFocusRing();

    const className = [
        classes.resizeIndicator,
        index === 0 ? classes.resizeIndicatorLeft : classes.resizeIndicatorRight,
        isActive ? classes.resizeIndicatorActive : '',
        isFocusVisible ? classes.resizeIndicatorFocussed : '',
    ].join(' ');

    if (showResizeIcons) {
        return (
            <div style={{ left: `${state.getThumbPercent(index) * 100}%` }} className={className} {...thumbProps}>
                {index === 0 ? (
                    <StartRageVideoThumb className={classes.startRangeIcon} aria-label='Start range' />
                ) : (
                    <EndRangeVideoThumb className={classes.endRangeIcon} aria-label='End range' />
                )}
                <VisuallyHidden>
                    <input ref={inputRef} {...mergeProps(inputProps, focusProps)} />
                </VisuallyHidden>
            </div>
        );
    }

    return <div style={{ left: `${state.getThumbPercent(index) * 100}%` }} className={className} {...thumbProps} />;
};

interface CreateRangeProps {
    minValue: number;
    maxValue: number;
    videoTimelineValue: number;
    range: [number, number] | null;
    setRange: (range: [number, number] | null) => void;
    labels: Label[];
    onSelectLabelForRange: (label: Label) => void;
    showResizeIcons?: boolean;
}

const START_RANGE_INDICATOR = 0;
const END_RANGE_INDICATOR = 2;
const THUMB_INDICATOR = 1;

export const CreateRange = ({
    labels,
    onSelectLabelForRange,
    videoTimelineValue,
    range,
    setRange,
    showResizeIcons = true,
    ...props
}: CreateRangeProps) => {
    // If the user did not start creating a new range we let the resize indicators
    // follow the video player's timeline slider
    const value =
        range === null
            ? [videoTimelineValue, videoTimelineValue, videoTimelineValue]
            : [range[0], videoTimelineValue, range[1]];

    const trackRef = useRef(null);
    const numberFormatter = useNumberFormatter({});

    const state = useSliderState({ ...props, numberFormatter, onChange, value });

    function onChange(newRange: number[]) {
        if (newRange.length !== 3) {
            return;
        }

        const [startRange, , endRange] = newRange;

        if (startRange === endRange) {
            setRange(null);
            return;
        }

        setRange([startRange, endRange]);
    }

    const { groupProps, trackProps } = useSlider({ ...props, 'aria-label': 'Create a new range' }, state, trackRef);

    const leftPercentage = state.getThumbPercent(START_RANGE_INDICATOR);
    const rightPercentage = state.getThumbPercent(END_RANGE_INDICATOR);
    const thumbPercentage = state.getThumbPercent(THUMB_INDICATOR);

    return (
        <>
            <div {...groupProps} className={classes.createRangeGroup}>
                <div {...trackProps} ref={trackRef} className={classes.createRangeTrack}>
                    <ResizeRangeThumb
                        showResizeIcons={showResizeIcons}
                        index={START_RANGE_INDICATOR}
                        state={state}
                        trackRef={trackRef}
                        isActive={range !== null}
                    />
                    <ResizeRangeThumb
                        showResizeIcons={showResizeIcons}
                        index={END_RANGE_INDICATOR}
                        state={state}
                        trackRef={trackRef}
                        isActive={range !== null}
                    />
                    <ThumbIndicator left={`${thumbPercentage * 100}%`} />
                </div>
            </div>
            {range !== null && (
                <RangeSection
                    leftPercentage={leftPercentage}
                    rightPercentage={rightPercentage}
                    labels={labels}
                    onSelectLabelForRange={onSelectLabelForRange}
                />
            )}
        </>
    );
};
