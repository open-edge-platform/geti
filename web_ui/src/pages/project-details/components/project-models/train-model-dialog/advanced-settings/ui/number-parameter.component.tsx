// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useEffect, useState } from 'react';

import { Flex, NumberField, Slider } from '@geti/ui';

import { getFloatingPointStep } from '../utils';

interface NumberGroupParamsProps {
    value: number;
    minValue: number;
    maxValue: number;
    onChange: (value: number) => void;
    type: 'integer' | 'float';
}

export const NumberParameter: FC<NumberGroupParamsProps> = ({ value, minValue, maxValue, type, onChange }) => {
    const [parameterValue, setParameterValue] = useState<number>(value);

    const floatingPointStep = getFloatingPointStep(minValue, maxValue);

    const step = type === 'integer' ? 1 : floatingPointStep;

    const handleValueChange = (inputValue: number): void => {
        setParameterValue(inputValue);
    };

    const handleSliderChangeEnd = (inputValue: number): void => {
        setParameterValue(inputValue);
        onChange(inputValue);
    };

    useEffect(() => {
        setParameterValue(value);
    }, [value]);

    return (
        <Flex gap={'size-100'}>
            <Slider
                value={parameterValue}
                minValue={minValue}
                maxValue={maxValue}
                onChange={handleValueChange}
                onChangeEnd={handleSliderChangeEnd}
                step={step}
                isFilled
                flex={1}
            />
            <NumberField
                isQuiet
                step={step}
                value={value}
                minValue={minValue}
                maxValue={maxValue}
                onChange={handleValueChange}
            />
        </Flex>
    );
};
