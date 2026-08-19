// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from 'react';

import { ActionButton, Flex, NumberField, Slider, Text, View } from '@geti-ui/ui';
import { Refresh } from '@geti-ui/ui/icons';

import classes from './confidence-threshold.module.scss';

const THRESHOLD_CONFIG = {
    defaultValue: 0.3,
    step: 0.001,
    min: 0,
    max: 1,
};

type ThresholdFieldProps = {
    name: string;
    onChange: (value: number) => void;
    isDisabled?: boolean;
    value: number;
};

const ThresholdField = ({ onChange, value, isDisabled, name }: ThresholdFieldProps) => {
    const [parameterValue, setParameterValue] = useState<number>(value);
    const previousValueRef = useRef<number>(value);

    if (previousValueRef.current !== value) {
        previousValueRef.current = value;
        setParameterValue(value);
    }

    const handleValueChange = (inputValue: number) => {
        setParameterValue(inputValue);
        onChange(inputValue);
    };

    return (
        <Flex gap={'size-100'}>
            <Slider
                aria-label={`Change ${name} slider`}
                value={parameterValue}
                minValue={THRESHOLD_CONFIG.min}
                maxValue={THRESHOLD_CONFIG.max}
                onChange={setParameterValue}
                onChangeEnd={onChange}
                step={THRESHOLD_CONFIG.step}
                isFilled
                flex={1}
                isDisabled={isDisabled}
            />
            <NumberField
                hideStepper
                width={'size-900'}
                value={parameterValue}
                minValue={THRESHOLD_CONFIG.min}
                maxValue={THRESHOLD_CONFIG.max}
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
    const defaultValue = THRESHOLD_CONFIG.defaultValue;
    const [threshold, setThreshold] = useState<number>(defaultValue);

    return (
        <View>
            <Text UNSAFE_className={classes.label}>Confidence threshold</Text>
            <Flex width={'100%'} gap={'size-175'} alignItems={'center'}>
                <ThresholdField
                    onChange={setThreshold}
                    name={'Confidence threshold'}
                    value={threshold}
                    isDisabled={isDisabled}
                />
                <ActionButton
                    isQuiet
                    aria-label={'Reset confidence threshold'}
                    onPress={() => setThreshold(defaultValue)}
                    isDisabled={isDisabled}
                >
                    <Refresh />
                </ActionButton>
            </Flex>
        </View>
    );
};
