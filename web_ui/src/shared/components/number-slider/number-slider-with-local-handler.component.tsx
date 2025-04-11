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

import { useState } from 'react';

import { NumberSlider, NumberSliderProps } from './number-slider.component';

interface NumberSliderWithLocalHandlerProps {
    changeAdHoc?: boolean;
}
export const NumberSliderWithLocalHandler = ({
    value: defaultValue,
    onChange,
    isInputEditable,
    changeAdHoc = false,
    ...props
}: NumberSliderProps & NumberSliderWithLocalHandlerProps): JSX.Element => {
    const [value, setValue] = useState<number>(defaultValue);

    const onChangeHandler = (newValue: number) => {
        setValue(newValue);
        onChange(newValue);
    };

    const parameters = changeAdHoc
        ? {
              onChange: onChangeHandler,
          }
        : { onChange: setValue, onChangeEnd: onChange };

    return <NumberSlider {...props} value={value} {...parameters} isInputEditable={isInputEditable} />;
};
