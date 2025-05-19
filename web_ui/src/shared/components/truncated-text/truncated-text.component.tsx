// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, CSSProperties } from 'react';

import { PressableElement, Tooltip, TooltipTrigger, useStyleProps, type StyleProps } from '@geti/ui';
import { PositionProps } from 'react-aria';

import { idMatchingFormat } from '../../../test-utils/id-utils';

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
    ComponentProps<typeof PressableElement>;

//ActionElement stops event propagation https://github.com/adobe/react-spectrum/issues/2100
export const TruncatedTextWithTooltip = ({
    children,
    placement = 'bottom',
    ...others
}: TruncatedTextWithTooltipProps): JSX.Element => {
    return (
        <TooltipTrigger placement={placement}>
            <PressableElement {...others} isTruncated>
                {children}
            </PressableElement>
            <Tooltip>{children}</Tooltip>
        </TooltipTrigger>
    );
};
