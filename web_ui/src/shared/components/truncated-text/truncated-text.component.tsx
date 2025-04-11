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

import { CSSProperties, ReactNode } from 'react';

import { SpectrumActionButtonProps, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { useStyleProps } from '@react-spectrum/utils';
import { StyleProps } from '@react-types/shared';
import { PositionProps } from 'react-aria';

import { idMatchingFormat } from '../../../test-utils/id-utils';
import { ActionElement } from '../action-element/action-element.component';

const TruncatedTextStyles: CSSProperties = {
    display: 'block',
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
};

interface TruncatedTextProps extends StyleProps {
    id?: string;
    'aria-label'?: string;
    'data-testid'?: string;
    children: string;
}

export const TruncatedText = ({ id, children, ...otherProps }: TruncatedTextProps): JSX.Element => {
    const { styleProps } = useStyleProps(otherProps);

    return (
        <span
            className={styleProps.className}
            id={id ?? idMatchingFormat(children)}
            style={{ ...styleProps.style, ...TruncatedTextStyles }}
            data-testid={otherProps['data-testid']}
            aria-label={otherProps['aria-label']}
            title={children}
        >
            {children}
        </span>
    );
};

type TruncatedTextWithTooltipProps = StyleProps &
    PositionProps &
    Omit<TruncatedTextProps, 'classes' | 'children'> &
    Omit<SpectrumActionButtonProps, 'isQuiet'> & { children: ReactNode };

//ActionElement stops event propagation https://github.com/adobe/react-spectrum/issues/2100
export const TruncatedTextWithTooltip = ({
    children,
    placement = 'bottom',
    ...others
}: TruncatedTextWithTooltipProps): JSX.Element => {
    return (
        <TooltipTrigger placement={placement}>
            <ActionElement {...others} isTruncated>
                {children}
            </ActionElement>
            <Tooltip>{children}</Tooltip>
        </TooltipTrigger>
    );
};
