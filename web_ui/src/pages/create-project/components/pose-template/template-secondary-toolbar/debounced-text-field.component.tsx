// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SpectrumTextFieldProps, TextField } from '@geti/ui';

import { useDebouncedCallback } from '../../../../../hooks/use-debounced-callback/use-debounced-callback.hook';

interface DebouncedTextFieldProps extends SpectrumTextFieldProps {
    delay?: number;
    onChange: (value: string) => void;
    onChangeEnd: (value: string) => void;
}

export const DebouncedTextField = ({ onChange, onChangeEnd, delay = 200, ...props }: DebouncedTextFieldProps) => {
    const debouncedChangeEnded = useDebouncedCallback((newValue: string) => {
        onChangeEnd(newValue);
    }, delay);

    return (
        <TextField
            {...props}
            onChange={(value) => {
                onChange(value);
                debouncedChangeEnded(value);
            }}
        />
    );
};
