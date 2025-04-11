// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

import { Switch as SpectrumSwitch, SpectrumSwitchProps } from '@adobe/react-spectrum';

export const Switch = (props: SpectrumSwitchProps) => {
    const { UNSAFE_style, ...rest } = props;

    const styles = rest.isEmphasized
        ? {
              '--spectrum-switch-emphasized-track-color-selected': 'var(--energy-blue)',
              '--spectrum-switch-emphasized-track-color-selected-hover': 'var(--energy-blue-light)',
              '--spectrum-switch-emphasized-track-color-selected-down': 'var(--energy-blue-lighter)',
              '--spectrum-switch-emphasized-handle-border-color-selected': 'var(--energy-blue)',
              '--spectrum-switch-emphasized-handle-border-color-selected-hover': 'var(--energy-blue-light)',
              '--spectrum-switch-emphasized-handle-border-color-selected-down': 'var(--energy-blue-lighter)',
          }
        : {};

    return (
        <SpectrumSwitch
            {...rest}
            UNSAFE_style={
                {
                    ...UNSAFE_style,
                    ...styles,
                } as CSSProperties
            }
        />
    );
};
