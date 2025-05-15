// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/* eslint-disable no-restricted-imports */

import { ComponentProps, forwardRef, Ref } from 'react';

import {
    ActionButton as SpectrumActionButton,
    SpectrumActionButtonProps,
    Button as SpectrumButton,
    SpectrumButtonProps,
} from '@adobe/react-spectrum';
import { FocusableRef, FocusableRefValue } from '@react-types/shared';
import { Link } from 'react-router-dom';

type VariantWithoutLegacyButtonVariant = Exclude<SpectrumButtonProps['variant'], 'cta' | 'overBackground'>;

export interface ButtonProps extends Omit<SpectrumButtonProps, 'variant'> {
    ref?: FocusableRef<HTMLButtonElement>;
    variant?: VariantWithoutLegacyButtonVariant;
}

// https://github.com/adobe/react-spectrum/blob/main/packages/%40react-aria/button/src/useButton.ts#L75
// This component builds up a link with a fixed `to` prop,
// this used so that it can be used as `elementTYpe={LinkBuilder(href)}` in a react/spectrum
// button component, which does not forward an href for custom element types
type LinkProps = ComponentProps<typeof Link>;
function LinkBuilder({ href, target, rel }: { href: string; target?: LinkProps['target']; rel: LinkProps['rel'] }) {
    return forwardRef((props: LinkProps, ref: LinkProps['ref']) => {
        return <Link {...props} ref={ref} target={target} rel={rel} to={href} />;
    });
}

export interface ActionButtonProps extends SpectrumActionButtonProps {
    ref?: Ref<FocusableRefValue<HTMLElement, HTMLButtonElement>>;
}

export const Button = forwardRef((props: ButtonProps, ref: ButtonProps['ref']) => {
    const elementType =
        props.href === undefined
            ? props.elementType
            : LinkBuilder({ href: props.href, target: props.target, rel: props.rel });

    return <SpectrumButton {...props} elementType={elementType} variant={props.variant ?? 'accent'} ref={ref} />;
});

export const ActionButton = forwardRef((props: ActionButtonProps, ref: ActionButtonProps['ref']) => {
    return <SpectrumActionButton {...props} ref={ref} />;
});
