// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, CSSProperties, ReactNode } from 'react';

import { useStyleProps } from '@react-spectrum/utils';
import { StyleProps } from '@react-types/shared';
import { Pressable } from 'react-aria-components';

interface PressableElementProps extends Omit<ComponentProps<typeof Pressable>, 'children'>, StyleProps {
    id?: string;
    isTruncated?: boolean;
    onDoubleClick?: () => void;
    children: ReactNode;
}

const TruncatedTextStyles: CSSProperties = {
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
};

export const PressableElement = ({ id, children, isTruncated, onDoubleClick, ...props }: PressableElementProps) => {
    const { styleProps } = useStyleProps(props);
    const styles = isTruncated ? TruncatedTextStyles : {};

    return (
        <Pressable {...props}>
            <div id={id} {...styleProps} style={{ ...styles, ...styleProps.style }} onDoubleClick={onDoubleClick}>
                {children}
            </div>
        </Pressable>
    );
};
