// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, CSSProperties } from 'react';

import { Slider as SpectrumSlider } from '@adobe/react-spectrum';

export const Slider = (props: ComponentProps<typeof SpectrumSlider>) => {
    const isFilled = props.isFilled === true;

    const filledStyles = isFilled
        ? {
              '--spectrum-slider-fill-track-color': 'var(--energy-blue)',
              '--spectrum-slider-handle-border-color': 'var(--energy-blue)',
              '--spectrum-slider-handle-border-color-down': 'var(--energy-blue-lighter)',
              '--spectrum-slider-handle-border-color-hover': 'var(--energy-blue-light)',
          }
        : ({} as CSSProperties);

    return <SpectrumSlider {...props} UNSAFE_style={{ ...props.UNSAFE_style, ...filledStyles }} />;
};
