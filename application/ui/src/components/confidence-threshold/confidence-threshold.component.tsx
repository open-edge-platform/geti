// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from 'react';

import { ActionButton, Flex, NumberField, Slider, View } from '@geti-ui/ui';
import { Refresh } from '@geti-ui/ui/icons';

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
        <Flex gap={'size-100'} alignItems={'end'}>
            <Slider
                label={name}
                showValueLabel={false}
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

type ConfidenceThresholdProps = {
    isDisabled?: boolean;
    maxWidth?: string;
    width?: string;
};

export const ConfidenceThreshold = ({ isDisabled = false, maxWidth, width = '100%' }: ConfidenceThresholdProps) => {
    // TODO: Default confidence threshold value will come from the server side
    const defaultValue = THRESHOLD_CONFIG.defaultValue;
    const [threshold, setThreshold] = useState<number>(defaultValue);

    return (
        <View maxWidth={maxWidth} width={width}>
            <Flex width={'100%'} gap={'size-175'} alignItems={'end'}>
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
