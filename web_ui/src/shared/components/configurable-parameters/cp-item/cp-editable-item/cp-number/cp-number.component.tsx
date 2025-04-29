// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Flex, NumberField, Slider, Text, useNumberFormatter } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';

import { isLargeSizeQuery } from '../../../../../../theme/queries';
import { NumberGroupParams } from '../../../configurable-parameters.interface';
import { ResetButtonHandler } from '../cp-editable-item.interface';

import classes from './cp-number.module.scss';

interface CPNumberProps extends ResetButtonHandler {
    parameter: NumberGroupParams;
}

interface NumberFormatOptions {
    notation: 'compact' | 'standard' | 'scientific' | 'engineering' | undefined;
    compactDisplay: 'short' | 'long' | undefined;
    maximumFractionDigits: number;
}

const getDecimalPoints = (value: number, fieldName?: string): number => {
    const isSubsetSplittingField = fieldName?.endsWith('proportion');

    if (isSubsetSplittingField) {
        // We only want to show 2 decimals for subset splitting.
        return 2;
    }

    return Math.abs(Math.ceil(Math.log10(value)));
};

const getFloatingPointStep = (minValue: number, maxValue: number): number => {
    const exponent = getDecimalPoints(maxValue - minValue);

    return 1 / Math.pow(10, exponent + 3);
};

export const CPNumber = ({ id, parameter, updateParameter }: CPNumberProps): JSX.Element => {
    const { value, defaultValue, minValue, maxValue, id: parameterId, name } = parameter;
    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    const floatingPointStep = useMemo<number>(() => {
        return getFloatingPointStep(minValue, maxValue);
    }, [minValue, maxValue]);

    const step = parameter.dataType === 'integer' ? 1 : floatingPointStep;

    const formatterConfiguration: NumberFormatOptions = {
        notation: 'compact',
        compactDisplay: 'short',
        maximumFractionDigits: getDecimalPoints(step, name),
    };
    const formatter = useNumberFormatter(formatterConfiguration);

    const handleOnChange = (inputValue: number): void => {
        updateParameter && updateParameter(parameterId, inputValue);
    };

    const formatSliderLabel = (inputValue: number): string => formatter.format(inputValue);

    return (
        <Flex alignItems='center' marginEnd={'size-200'}>
            <NumberField
                value={value}
                defaultValue={defaultValue}
                onChange={handleOnChange}
                step={step}
                maxValue={maxValue}
                minValue={minValue}
                marginEnd={'size-450'}
                aria-label={'Select number in a range'}
                id={`${id}-number-field-id`}
            />

            {isLargeSize && (
                <Flex alignItems='center' gap='size-175' flex={1}>
                    <Text id={`${id}-min-value-id`} UNSAFE_className={classes.minMaxValues}>
                        {formatter.format(minValue)}
                    </Text>

                    <Slider
                        defaultValue={defaultValue}
                        minValue={minValue}
                        maxValue={maxValue}
                        isFilled
                        labelPosition={'top'}
                        value={value}
                        width={'calc(100% - 62px)'}
                        onChange={handleOnChange}
                        aria-label={'Select number in a slider'}
                        getValueLabel={formatSliderLabel}
                        marginX={{ base: '0', L: 'size-150' }}
                        step={step}
                        id={`${id}-slider-id`}
                        flex={1}
                    />

                    <Text id={`${id}-max-value-id`} UNSAFE_className={classes.minMaxValues}>
                        {formatter.format(maxValue)}
                    </Text>
                </Flex>
            )}
        </Flex>
    );
};
