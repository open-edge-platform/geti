// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ForwardedRef, forwardRef } from 'react';

import { TextField, type SpectrumTextFieldProps, type TextFieldRef } from '@geti/ui';

export const LimitedTextField = forwardRef(
    (props: SpectrumTextFieldProps, ref: ForwardedRef<TextFieldRef>): JSX.Element => {
        return <TextField {...props} ref={ref} maxLength={100} />;
    }
);
