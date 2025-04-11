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

import { ComponentProps, forwardRef, ReactNode } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { clsx } from 'clsx';
import isNil from 'lodash/isNil';
import { Placement } from 'react-aria';

import { Button } from '../button/button.component';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

import classes from './button-with-tooltip.module.scss';

type ButtonProps = Partial<ComponentProps<typeof Button>>;

interface ButtonWithSpectrumTooltip extends Partial<ButtonProps> {
    buttonClasses?: string;
    isClickable?: boolean;
    children: ReactNode;
    tooltipPlacement?: Placement;
    tooltip?: ReactNode | ReactNode[];
}

export const ButtonWithSpectrumTooltip = forwardRef((props: ButtonWithSpectrumTooltip, ref: ButtonProps['ref']) => {
    const {
        variant = 'secondary',
        buttonClasses,
        isClickable = false,
        children,
        tooltipPlacement,
        isQuiet,
        tooltip,
        ...rest
    } = props;

    const ButtonComponent = isQuiet ? QuietActionButton : Button;

    return (
        <TooltipTrigger placement={tooltipPlacement} isDisabled={isNil(tooltip)}>
            <ButtonComponent
                ref={ref}
                variant={variant}
                UNSAFE_className={clsx(buttonClasses, !isClickable ? classes.tooltipBtn : '')}
                {...rest}
            >
                {children}
            </ButtonComponent>
            <Tooltip>{tooltip}</Tooltip>
        </TooltipTrigger>
    );
});
