// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { DialogTrigger, Flex, Text, View } from '@adobe/react-spectrum';
import { ActionButton, Slider } from '@geti/ui';
import { noop } from 'lodash-es';

import { ChevronDownLight } from '../../../assets/icons';
import { CustomNumberField } from '../configurable-parameters/cp-item/custom-number-field/custom-number-field.component';

import classes from './number-slider.module.scss';

export interface NumberSliderProps {
    id: string;
    min: number;
    max: number;
    step: number;
    label?: string;
    width?: ComponentProps<typeof View>['width'];
    ariaLabel: string;
    isDisabled?: boolean;
    value: number;
    onChange: (value: number) => void;
    onChangeEnd?: (value: number) => void;
    displayText: (value: number) => string | number;
    UNSAFE_className?: string;
    isInputEditable?: boolean;
}

export const NumberSlider = ({
    id,
    min,
    max,
    step,
    label,
    width,
    onChange,
    onChangeEnd = noop,
    ariaLabel,
    displayText,
    value,
    isDisabled = false,
    UNSAFE_className,
    isInputEditable = false,
}: NumberSliderProps): JSX.Element => {
    const valueToDisplay = displayText(value).toString();

    return (
        <Flex alignItems='center' gap='size-100' UNSAFE_className={UNSAFE_className} data-testid={'slider-wrapper'}>
            {label && <Text UNSAFE_className={classes.text}>{label}:</Text>}
            <DialogTrigger type='popover'>
                <Flex>
                    {isInputEditable && (
                        <CustomNumberField
                            value={value}
                            minValue={min}
                            maxValue={max}
                            onChange={onChange}
                            isDisabled={isDisabled}
                            width={'size-600'}
                            height={'size-250'}
                            UNSAFE_className={classes.textField}
                            aria-label={`${ariaLabel} field`}
                            step={1}
                            disableStepArrow
                            isValueChangedAdHoc
                        />
                    )}
                    <ActionButton
                        aria-label={`${ariaLabel} button`}
                        data-testid={`${id}-button`}
                        id={`${id}-button`}
                        minWidth={isInputEditable ? 'size-125' : 'size-350'}
                        height={'size-250'}
                        isDisabled={isDisabled}
                        UNSAFE_className={isInputEditable ? classes.editableInputSliderButton : classes.sliderButton}
                    >
                        {!isInputEditable && <Text UNSAFE_className={classes.text}>{valueToDisplay}</Text>}
                        <ChevronDownLight style={{ order: 1 }} />
                    </ActionButton>
                </Flex>
                <View width={width} paddingTop='size-65' paddingX='size-75' paddingBottom='size-40'>
                    <Flex alignItems={'center'} direction={'column'}>
                        <Slider
                            step={step}
                            value={value}
                            minValue={min}
                            maxValue={max}
                            id={`${id}-slider`}
                            onChange={onChange}
                            showValueLabel={false}
                            onChangeEnd={onChangeEnd}
                            isDisabled={isDisabled}
                            aria-label={`${ariaLabel} slider`}
                        />
                    </Flex>
                </View>
            </DialogTrigger>
        </Flex>
    );
};
