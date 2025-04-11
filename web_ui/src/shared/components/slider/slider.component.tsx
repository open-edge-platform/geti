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
