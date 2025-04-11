// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
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

import { ActionButton } from '../button/button.component';

import sharedClasses from '../../shared.module.scss';

export enum ColorMode {
    DARK,
    LIGHT,
    BLUE,
}

interface QuietActionButtonProps extends Omit<SpectrumActionButtonProps, 'isQuiet'> {
    colorMode?: ColorMode;
}

export const QuietActionButton = forwardRef((props: QuietActionButtonProps, ref: FocusableRef<HTMLButtonElement>) => {
    const { colorMode = ColorMode.DARK, ...rest } = props;

    const buttonClass =
        colorMode === ColorMode.DARK
            ? sharedClasses.actionButtonDark
            : colorMode === ColorMode.LIGHT
              ? sharedClasses.actionButtonLight
              : sharedClasses.actionButtonBlue;

    return (
        <ActionButton isQuiet ref={ref} {...rest} UNSAFE_className={`${buttonClass} ${props.UNSAFE_className ?? ''}`} />
    );
});
