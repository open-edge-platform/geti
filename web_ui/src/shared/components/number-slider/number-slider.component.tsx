// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps } from 'react';

import { DialogTrigger, Flex, Slider, View } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';
import noop from 'lodash/noop';

import { ChevronDownLight } from '../../../assets/icons';
import { ActionButton } from '../button/button.component';
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
