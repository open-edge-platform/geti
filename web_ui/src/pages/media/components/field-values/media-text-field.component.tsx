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

import { useEffect, useMemo, useState } from 'react';

import { TextField } from '@adobe/react-spectrum';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { useDebouncedCallback } from '../../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { textRegex } from '../../utils';

interface MediaTextFieldProps {
    value?: string;
    isDisabled?: boolean;
    ariaLabel: string;
    placeholder?: string;
    onSelectionChange: (key: SearchRuleValue) => void;
}

export const MediaTextField = ({
    value: initVal = '',
    isDisabled = false,
    placeholder = '',
    onSelectionChange,
    ariaLabel,
}: MediaTextFieldProps): JSX.Element => {
    const [value, setValue] = useState(initVal);

    const isValid = useMemo(() => textRegex.test(value), [value]);

    useEffect(() => {
        setValue((prev) => (initVal !== prev ? initVal : prev));
    }, [initVal]);

    const onDebounceSelectionChange = useDebouncedCallback((newValue: string) => {
        onSelectionChange(newValue);
    }, 500);

    const onSetValue = (newValue: string) => {
        setValue(newValue);

        onDebounceSelectionChange(newValue);
    };

    return (
        <TextField
            isQuiet
            value={value}
            aria-label={ariaLabel}
            width={'100%'}
            onChange={onSetValue}
            isDisabled={isDisabled}
            placeholder={placeholder}
            id={idMatchingFormat(ariaLabel)}
            validationState={isDisabled || isValid ? 'valid' : 'invalid'}
        />
    );
};
