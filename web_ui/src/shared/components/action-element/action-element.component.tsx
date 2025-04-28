// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import React, { ComponentProps, CSSProperties, forwardRef } from 'react';

import { SpectrumActionButtonProps, Text } from '@adobe/react-spectrum';
import { useFocusableRef, useStyleProps } from '@react-spectrum/utils';
import { FocusableRef, StyleProps } from '@react-types/shared';
import { FocusRing, useButton } from 'react-aria';
import { Pressable } from 'react-aria-components';

interface PressableElementProps extends ComponentProps<typeof Pressable>, StyleProps {
    id?: string;
}

interface ActionElementProps extends Omit<SpectrumActionButtonProps, 'isQuiet'> {
    id?: string;
    isTruncated?: boolean;
    onDoubleClick?: () => void;
}

const TruncatedTextStyles: CSSProperties = {
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
};

export const ActionElement = forwardRef((props: ActionElementProps, ref: FocusableRef<HTMLDivElement>) => {
    const { children, isTruncated, onDoubleClick, ...otherProps } = props;

    const domRef = useFocusableRef(ref);
    const { buttonProps } = useButton(props, domRef);
    const { styleProps } = useStyleProps(otherProps);
    const isTextOnly = React.Children.toArray(props.children).every((child) => !React.isValidElement(child));
    const styles = isTruncated ? TruncatedTextStyles : {};

    return (
        <FocusRing>
            <div
                ref={domRef}
                {...buttonProps}
                {...styleProps}
                style={{ ...styles, ...styleProps.style }}
                onDoubleClick={onDoubleClick}
            >
                {typeof children === 'string' || isTextOnly ? <Text>{children}</Text> : <>{children}</>}
            </div>
        </FocusRing>
    );
});

export const PressableElement = ({ id, children, ...props }: PressableElementProps) => {
    const { styleProps } = useStyleProps(props);

    return (
        <Pressable {...props}>
            <div role='button' id={id} {...styleProps}>
                {children}
            </div>
        </Pressable>
    );
};
