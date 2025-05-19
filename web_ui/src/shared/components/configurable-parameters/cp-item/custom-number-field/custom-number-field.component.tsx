// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FocusEvent, KeyboardEvent, useCallback, useEffect, useMemo, useState } from 'react';

import { ActionGroup, DimensionValue, Flex, Item, TextField, useNumberFormatter } from '@geti/ui';
import { Responsive } from '@react-types/shared';
import { SpectrumTextFieldProps } from '@react-types/textfield';

import { ChevronDownLight, ChevronUpLight } from '../../../../../assets/icons';
import { useDebouncedCallback } from '../../../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { usePrevious } from '../../../../../hooks/use-previous/use-previous.hook';
import { KeyMap } from '../../../../keyboard-events/keyboard.interface';

import classes from './custom-number-field.module.scss';

// Omit attributes which were string typed - we use number here
type TextFieldWithoutValue = Omit<SpectrumTextFieldProps, 'value' | 'defaultValue' | 'onChange'>;

interface CustomNumberFieldProps extends TextFieldWithoutValue {
    defaultValue?: number;
    value: number;
    onChange: (newValue: number) => void;
    step: number;
    id?: string;
    maxValue?: number;
    minValue: number;
    formatOptions?: Intl.NumberFormatOptions;
    disableStepArrow?: boolean;
    isValueChangedAdHoc?: boolean;
    TextFieldWidth?: Responsive<DimensionValue>;
}

enum Operation {
    INCREASE,
    DECREASE,
}

export const CustomNumberField = ({
    defaultValue,
    value,
    onChange,
    step,
    id,
    maxValue,
    minValue,
    formatOptions = { notation: 'standard', maximumFractionDigits: 2 },
    marginEnd,
    disableStepArrow,
    isValueChangedAdHoc,
    TextFieldWidth = 'size-1200',
    UNSAFE_className,
    ...inputProps
}: CustomNumberFieldProps): JSX.Element => {
    const [inputValue, setInputValue] = useState<number>(value);
    const [displayValue, setDisplayValue] = useState<string>(value.toString());
    const formatter = useNumberFormatter(formatOptions);
    const [isInputFocused, setIsInputFocused] = useState<boolean>(false);

    const isValid = !(inputProps.validationState && inputProps.validationState === 'invalid');

    const parseFloat = (parsingValue: string): number => {
        if (parsingValue.includes('%')) {
            return Number.parseFloat(parsingValue.replace('%', '')) / 100;
        }

        const parsed = Number.parseFloat(parsingValue.replaceAll(',', ''));

        if (parsingValue.includes('T')) {
            return parsed * 1e12;
        } else if (parsingValue.includes('B')) {
            return parsed * 1e9;
        } else if (parsingValue.includes('M')) {
            return parsed * 1e6;
        } else if (parsingValue.includes('K')) {
            return parsed * 1e3;
        }

        return parsed;
    };

    const previousValue = usePrevious(value);
    useEffect(() => {
        if (previousValue === value) {
            return;
        }

        setInputValue(value);
        setDisplayValue(formatter.format(value));
    }, [value, formatter, previousValue]);

    const disabledKeys = useMemo(() => {
        if (inputProps.isDisabled) {
            return ['up', 'down'];
        }

        if (inputValue === maxValue) {
            return ['up'];
        }

        if (inputValue === minValue) {
            return ['down'];
        }
    }, [inputValue, minValue, maxValue, inputProps.isDisabled]);

    const doOperation = (operation: Operation) => {
        const formattedChangedValue = formatter.format(
            operation === Operation.INCREASE
                ? maxValue
                    ? Math.min(maxValue, inputValue + step)
                    : inputValue + step
                : Math.max(minValue, inputValue - step)
        );
        const changedValue = parseFloat(formattedChangedValue);

        onChange(changedValue);
        setInputValue(changedValue);
        setDisplayValue(formattedChangedValue);
    };

    const increase = () => {
        doOperation(Operation.INCREASE);
        inputFocusChangeHandler(true);
    };

    const decrease = () => {
        doOperation(Operation.DECREASE);
        inputFocusChangeHandler(true);
    };

    const roundToMultipleOfStep = (numberValue: number, stepValue: number): number => {
        return stepValue * Math.round(numberValue / stepValue);
    };

    const acceptValue = useCallback((numberValue: number) => {
        if (!Number.isNaN(numberValue)) {
            const multiple = roundToMultipleOfStep(numberValue, step);

            const properValue = maxValue && multiple > maxValue ? maxValue : multiple < minValue ? minValue : multiple;

            onChange(properValue);
            setInputValue(properValue);
            setDisplayValue(formatter.format(properValue));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const acceptValueDebounced = useDebouncedCallback(acceptValue, 500);

    const onBlurHandler = (event: FocusEvent) => {
        const textValue = (event.target as HTMLInputElement).value;
        const numberValue = parseFloat(textValue);

        inputFocusChangeHandler(false);
        acceptValue(numberValue);
    };

    const inputFocusChangeHandler = (isFocused: boolean) => {
        setIsInputFocused(isFocused);
    };

    const handleOnChange = (newValue: string): void => {
        if (!Number.isNaN(parseFloat(newValue)) || !newValue) {
            setDisplayValue(newValue);
        }

        isValueChangedAdHoc && acceptValueDebounced(parseFloat(newValue));
    };

    const handleOnKeyDown = (event: KeyboardEvent) => {
        const newValue = (event.target as HTMLInputElement).value;

        if (event.key === KeyMap.Enter) {
            if (!Number.isNaN(parseFloat(newValue)) || !newValue) {
                setDisplayValue(newValue);
                acceptValue(parseFloat(newValue));
            }
        }
    };

    return (
        <Flex width={inputProps.width}>
            <TextField
                value={displayValue}
                onChange={handleOnChange}
                defaultValue={defaultValue?.toString()}
                maxWidth={TextFieldWidth}
                minWidth={'size-400'}
                onBlur={onBlurHandler}
                onFocusChange={inputFocusChangeHandler}
                onKeyDown={handleOnKeyDown}
                UNSAFE_className={`${classes.input} ${UNSAFE_className ?? ''} ${isInputFocused ? classes.focused : ''}`}
                id={id}
                {...inputProps}
            />

            {!disableStepArrow && (
                <ActionGroup
                    orientation='vertical'
                    density={'compact'}
                    margin={0}
                    UNSAFE_className={`${classes.actionGroup} ${isInputFocused ? classes.groupFocused : ''} ${
                        inputProps.isQuiet ? classes.isQuiet : ''
                    } ${isValid ? '' : classes.arrowsInvalidBorder}`}
                    height={'single-line-height'}
                    onAction={(key) => (key === 'up' ? increase() : decrease())}
                    disabledKeys={disabledKeys}
                    marginEnd={marginEnd}
                >
                    <Item key={'up'} aria-label={`Increase value`}>
                        <ChevronUpLight className={classes.icon} />
                    </Item>
                    <Item key={'down'} aria-label={`Decrease value`}>
                        <ChevronDownLight className={classes.icon} />
                    </Item>
                </ActionGroup>
            )}
        </Flex>
    );
};
