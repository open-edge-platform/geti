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

import { ForwardedRef, forwardRef } from 'react';

import { TextField } from '@adobe/react-spectrum';
import { SpectrumTextFieldProps, TextFieldRef } from '@react-types/textfield';

export const LimitedTextField = forwardRef(
    (props: SpectrumTextFieldProps, ref: ForwardedRef<TextFieldRef>): JSX.Element => {
        return <TextField {...props} ref={ref} maxLength={100} />;
    }
);
