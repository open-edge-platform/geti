// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
