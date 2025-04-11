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

/* eslint-disable no-restricted-imports */

import { forwardRef, Ref } from 'react';

import {
    ActionButton as SpectrumActionButton,
    SpectrumActionButtonProps,
    Button as SpectrumButton,
    SpectrumButtonProps,
} from '@adobe/react-spectrum';
import { FocusableRef, FocusableRefValue } from '@react-types/shared';

type VariantWithoutLegacyButtonVariant = Exclude<SpectrumButtonProps['variant'], 'cta' | 'overBackground'>;

export interface ButtonProps extends Omit<SpectrumButtonProps, 'variant'> {
    ref?: FocusableRef<HTMLButtonElement>;
    variant?: VariantWithoutLegacyButtonVariant;
}

export interface ActionButtonProps extends SpectrumActionButtonProps {
    ref?: Ref<FocusableRefValue<HTMLElement, HTMLButtonElement>>;
}

export const Button = forwardRef((props: ButtonProps, ref: ButtonProps['ref']) => {
    return <SpectrumButton {...props} variant={props.variant ?? 'accent'} ref={ref} />;
});

export const ActionButton = forwardRef((props: ActionButtonProps, ref: ActionButtonProps['ref']) => {
    return <SpectrumActionButton {...props} ref={ref} />;
});
