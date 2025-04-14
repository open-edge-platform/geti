// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
