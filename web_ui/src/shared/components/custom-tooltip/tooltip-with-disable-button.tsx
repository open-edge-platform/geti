// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isValidElement, ReactElement } from 'react';

import { SpectrumActionButtonProps, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import { Placement } from 'react-aria';

import { ActionElement } from '../action-element/action-element.component';

interface TooltipWithDisableButtonProps extends Omit<SpectrumActionButtonProps, 'isQuiet'> {
    children: ReactElement;
    activeTooltip?: ReactElement | string;
    disabledTooltip?: ReactElement | string;
    placement?: Placement;
}

export const TooltipWithDisableButton = ({
    children,
    placement = 'bottom',
    activeTooltip,
    disabledTooltip,
    ...props
}: TooltipWithDisableButtonProps): JSX.Element => {
    const showDisabledTooltip =
        'isDisabled' in children.props ? children.props.isDisabled : 'disabled' in children.props;

    return (
        <TooltipTrigger placement={placement} isDisabled={!showDisabledTooltip || isEmpty(disabledTooltip)}>
            <ActionElement {...props}>
                <TooltipTrigger placement={placement} isDisabled={isEmpty(activeTooltip)}>
                    {children}
                    {isValidElement(activeTooltip) ? activeTooltip : <Tooltip>{activeTooltip}</Tooltip>}
                </TooltipTrigger>
            </ActionElement>
            {isValidElement(disabledTooltip) ? disabledTooltip : <Tooltip>{disabledTooltip}</Tooltip>}
        </TooltipTrigger>
    );
};
