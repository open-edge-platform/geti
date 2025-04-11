// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { forwardRef } from 'react';

import { SpectrumActionButtonProps } from '@react-types/button';
import { FocusableRef } from '@react-types/shared';

import { ActionButton } from '../../../../../../shared/components/button/button.component';

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
