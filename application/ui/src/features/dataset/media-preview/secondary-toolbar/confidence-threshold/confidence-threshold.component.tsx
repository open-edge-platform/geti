// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from 'react';

import { ActionButton, Flex, NumberField, Slider, Text, View } from '@geti-ui/ui';
import { Refresh } from '@geti-ui/ui/icons';

import classes from './confidence-threshold.module.scss';

const THRESHOLD_CONFIG = {
    DEFAULT_VALUE: 0.3,
    step: 0.001,
    min: 0,
    max: 1,
};

type NumberGroupParamsProps = {
    name: string;
    onChange: (value: number) => void;
    isDisabled?: boolean;
    sliderWidth?: string;
    value: number;
    minValue: number | null;
    maxValue: number | null;
};

const NumberParameterField = ({
    minValue,
    maxValue,
    sliderWidth = 'size-2400',
    onChange,
    value,
    isDisabled,
    name,
}: NumberGroupParamsProps) => {
    const [parameterValue, setParameterValue] = useState<number>(value);
    const previousValueRef = useRef<number>(value);

    if (previousValueRef.current !== value) {
        previousValueRef.current = value;
        setParameterValue(value);
    }

    const handleValueChange = (inputValue: number): void => {
        setParameterValue(inputValue);
        onChange(inputValue);
    };

    if (maxValue === null || minValue === null) {
        return (
            <NumberField
                aria-label={`Change ${name}`}
                hideStepper
                width={'size-900'}
                value={parameterValue}
                minValue={minValue === null ? undefined : minValue}
                maxValue={maxValue === null ? undefined : maxValue}
                onChange={onChange}
                isDisabled={isDisabled}
                step={THRESHOLD_CONFIG.step}
            />
        );
    }

    return (
        <Flex gap={'size-100'}>
            <Slider
                aria-label={`Change ${name} slider`}
                value={parameterValue}
                minValue={minValue}
                maxValue={maxValue}
                onChange={setParameterValue}
                onChangeEnd={onChange}
                step={THRESHOLD_CONFIG.step}
                isFilled
                flex={1}
                width={sliderWidth ?? undefined}
                isDisabled={isDisabled}
            />
            <NumberField
                hideStepper
                width={'size-900'}
                value={parameterValue}
                minValue={minValue}
                maxValue={maxValue}
                onChange={handleValueChange}
                isDisabled={isDisabled}
                aria-label={`Change ${name}`}
                step={THRESHOLD_CONFIG.step}
            />
        </Flex>
    );
};

export const ConfidenceThreshold = ({ isDisabled }: { isDisabled: boolean }) => {
    // TODO: Default confidence threshold value will come from the server side
    const defaultValue = THRESHOLD_CONFIG.DEFAULT_VALUE;

    const handleResetThreshold = () => {
        // Reset the confidence threshold to its default value
    };

    return (
        <View>
            <Text UNSAFE_className={classes.label}>Confidence threshold</Text>
            <Flex width={'100%'} gap={'size-175'} alignItems={'center'}>
                <NumberParameterField
                    onChange={() => {}}
                    name={'Confidence threshold'}
                    minValue={THRESHOLD_CONFIG.min}
                    maxValue={THRESHOLD_CONFIG.max}
                    value={defaultValue}
                    isDisabled={isDisabled}
                />
                <ActionButton isQuiet onPress={handleResetThreshold} isDisabled={isDisabled}>
                    <Refresh />
                </ActionButton>
            </Flex>
        </View>
    );
};
