// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { useDebouncedCallback } from '../../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { CustomNumberField } from '../../../../shared/components/configurable-parameters/cp-item/custom-number-field/custom-number-field.component';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { isValidInteger } from '../../utils';

import classes from './media-integer-field.module.scss';

interface MediaIntegerFieldProps {
    initialValue: number;
    ariaLabel: string;
    isDisabled: boolean | undefined;
    onSelectionChange: (key: SearchRuleValue) => void;
}

export const MediaIntegerField = ({
    initialValue,
    ariaLabel,
    isDisabled,
    onSelectionChange,
}: MediaIntegerFieldProps): JSX.Element => {
    const [value, setValue] = useState<number | undefined>(initialValue);

    const onDebounceSelectionChange = useDebouncedCallback((newValue: number) => {
        onSelectionChange(Number(newValue));
    }, 500);

    const handleChangeValue = (newValue: number) => {
        setValue(newValue);

        if (isValidInteger(newValue)) {
            onDebounceSelectionChange(newValue);
        }
    };

    const isValid = isValidInteger(value);

    return (
        <CustomNumberField
            isQuiet
            width={'100%'}
            value={Number(value)}
            minValue={0}
            step={1}
            TextFieldWidth={'100%'}
            aria-label={ariaLabel}
            onChange={handleChangeValue}
            isDisabled={isDisabled}
            id={idMatchingFormat(ariaLabel)}
            validationState={isDisabled || isValid ? 'valid' : 'invalid'}
            errorMessage={
                !isValid ? (
                    <span
                        id={'media-integer-error-id'}
                        data-testid={'media-integer-error-id'}
                        className={classes.noWrap}
                    >
                        Maximum number is 2<sup>53</sup> -1
                    </span>
                ) : (
                    ''
                )
            }
        />
    );
};
