// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { SpectrumTextFieldProps, TextField } from '@adobe/react-spectrum';

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
