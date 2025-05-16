// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isValidElement, ReactElement } from 'react';

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { PressableElement } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { Placement } from 'react-aria';

interface TooltipWithDisableButtonProps {
    activeTooltip?: ReactElement | string;
    disabledTooltip?: ReactElement | string;
    placement?: Placement;
    children: ReactElement;
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

    const Element = (
        <TooltipTrigger placement={placement} isDisabled={isEmpty(activeTooltip)}>
            {children}
            {isValidElement(activeTooltip) ? activeTooltip : <Tooltip>{activeTooltip}</Tooltip>}
        </TooltipTrigger>
    );

    if (showDisabledTooltip && !isEmpty(disabledTooltip)) {
        return (
            <TooltipTrigger placement={placement}>
                <PressableElement {...props} aria-label='disabled tooltip trigger'>
                    {Element}
                </PressableElement>
                {isValidElement(disabledTooltip) ? disabledTooltip : <Tooltip>{disabledTooltip}</Tooltip>}
            </TooltipTrigger>
        );
    }

    return Element;
};
