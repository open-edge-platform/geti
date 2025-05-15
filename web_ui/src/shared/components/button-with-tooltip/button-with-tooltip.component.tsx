// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { forwardRef, ReactNode } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Button, type ButtonProps } from '@geti/ui';
import { clsx } from 'clsx';
import { isNil } from 'lodash-es';
import { Placement } from 'react-aria';

import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

import classes from './button-with-tooltip.module.scss';

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
