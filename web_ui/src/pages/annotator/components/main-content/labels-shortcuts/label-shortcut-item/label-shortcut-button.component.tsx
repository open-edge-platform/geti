// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { forwardRef } from 'react';

import { SpectrumActionButtonProps } from '@react-types/button';
import { FocusableRef } from '@react-types/shared';
import { ActionButton } from '@shared/components/button/button.component';

import classes from './label-shortcut-button.module.scss';

export const LabelShortcutButton = forwardRef(
    (
        { children, id, onPress, UNSAFE_className, ...rest }: SpectrumActionButtonProps,
        ref: FocusableRef<HTMLButtonElement>
    ): JSX.Element => {
        return (
            <ActionButton
                id={id}
                onPress={onPress}
                UNSAFE_className={`${
                    rest.isDisabled ? classes.labelDisabledButton : classes.labelButton
                } ${UNSAFE_className}`}
                {...rest}
                ref={ref}
            >
                {children}
            </ActionButton>
        );
    }
);
