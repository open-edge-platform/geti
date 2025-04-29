// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ForwardedRef, forwardRef } from 'react';

import { ToggleButton } from '@adobe/react-spectrum';
import { SpectrumToggleButtonProps } from '@react-types/button';
import { FocusableRefValue } from '@react-types/shared';

import sharedClasses from '../../shared.module.scss';

export const QuietToggleButton = forwardRef(
    (props: SpectrumToggleButtonProps, ref: ForwardedRef<FocusableRefValue<HTMLButtonElement, HTMLButtonElement>>) => (
        <ToggleButton
            isQuiet
            {...props}
            ref={ref}
            UNSAFE_className={`${sharedClasses.actionButtonDark} ${props.UNSAFE_className ?? ''}`}
        />
    )
);
