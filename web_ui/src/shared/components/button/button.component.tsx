// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
