// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
