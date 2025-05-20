// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, RefObject, useRef } from 'react';

import { Flex, Text, View, VisuallyHidden } from '@geti/ui';
import clsx from 'clsx';
import { mergeProps, useFocusRing, useNumberFormatter, useSlider, useSliderThumb } from 'react-aria';
import { SliderState, useSliderState } from 'react-stately';

import { Tooltip } from '../../../ui/tooltip.component';

import styles from './subsets-distribution-slider.module.scss';

interface ThumbProps {
    index: number;
    state: SliderState;
    trackRef: RefObject<HTMLDivElement>;
}

const Thumb: FC<ThumbProps> = (props) => {
    const { state, trackRef, index } = props;
    const inputRef = useRef(null);
    const { thumbProps, inputProps } = useSliderThumb(
        {
            index,
            trackRef,
            inputRef,
        },
        state
    );

    const { focusProps } = useFocusRing();

    return (
        <div
            {...thumbProps}
            className={styles.thumb}
            style={{
                left: `${state.getThumbPercent(index) * 100}%`,
            }}
        >
            <VisuallyHidden>
                <input ref={inputRef} {...mergeProps(inputProps, focusProps)} />
            </VisuallyHidden>
        </div>
    );
};

const DistributionTooltip: FC = () => {
    return (
        <Tooltip>
            Specify the distribution of annotated samples over the training, validation and test subsets. Note: items
            that have already been used for training will stay in the same subset even if these parameters are changed.
        </Tooltip>
    );
};

interface SubsetsDistributionSliderProps {
    label: string;
    onChangeEnd?: (values: number[] | number) => void;
    value: number | number[];
    defaultValue?: number | number[];
    onChange: (values: number[] | number) => void;
    maxValue: number;
    step: number;
    minValue: number;
    formatOptions?: Intl.NumberFormatOptions;
}

export const SubsetsDistributionSlider = (props: SubsetsDistributionSliderProps) => {
    const trackRef = useRef(null);

    const numberFormatter = useNumberFormatter(props.formatOptions);
    const state = useSliderState({ ...props, numberFormatter });
    const { trackProps, labelProps } = useSlider(props, state, trackRef);

    const trainingValue = parseInt(state.getThumbValueLabel(0));
    const validationValue = parseInt(state.getThumbValueLabel(1)) - parseInt(state.getThumbValueLabel(0));
    const testValue = props.maxValue - trainingValue - validationValue;

    return (
        <>
            <View gridArea={'label'}>
                <label {...labelProps}>
                    {props.label} <DistributionTooltip />
                </label>
            </View>
            <Flex gridArea={'slider'} alignItems={'center'} gap={'size-150'}>
                <div {...trackProps} ref={trackRef} className={styles.trackContainer}>
                    <View
                        width={`${state.getThumbPercent(0) * 100}%`}
                        UNSAFE_className={clsx(styles.track, styles.trainingTrack)}
                    />
                    <View
                        width={`${(state.getThumbPercent(1) - state.getThumbPercent(0)) * 100}%`}
                        left={`${state.getThumbPercent(0) * 100}%`}
                        UNSAFE_className={clsx(styles.track, styles.validationTrack)}
                    />
                    <View
                        width={`${100 - state.getThumbPercent(1) * 100}%`}
                        left={`${state.getThumbPercent(1) * 100}%`}
                        UNSAFE_className={clsx(styles.track, styles.testTrack)}
                    />
                    <Thumb index={0} state={state} trackRef={trackRef} />
                    <Thumb index={1} state={state} trackRef={trackRef} />
                </div>
                <Text width={'size-1000'}>
                    {trainingValue}/{validationValue}/{testValue}%
                </Text>
            </Flex>
        </>
    );
};
