// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
