// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { forwardRef } from 'react';

import { ActionButton, type ActionButtonProps } from '@geti/ui';
import { FocusableRef } from '@react-types/shared';

import classes from './label-shortcut-button.module.scss';

export const LabelShortcutButton = forwardRef(
    (
        { children, id, onPress, UNSAFE_className, ...rest }: ActionButtonProps,
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
