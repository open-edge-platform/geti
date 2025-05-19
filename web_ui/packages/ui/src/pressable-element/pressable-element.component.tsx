// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, CSSProperties, ReactNode } from 'react';

import { useStyleProps, viewStyleProps } from '@react-spectrum/utils';
import { StyleProps } from '@react-types/shared';
import { omit } from 'lodash-es';
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

const viewStyleKeys = [...Object.keys(viewStyleProps), 'UNSAFE_className', 'UNSAFE_style'];

export const PressableElement = ({ id, children, isTruncated, onDoubleClick, ...props }: PressableElementProps) => {
    const styles = isTruncated ? TruncatedTextStyles : {};
    const pressableProps = omit(props, viewStyleKeys);
    const { styleProps } = useStyleProps(props);

    return (
        <Pressable {...pressableProps}>
            <div
                id={id}
                {...styleProps}
                style={{ ...styles, ...styleProps.style }}
                onDoubleClick={onDoubleClick}
                role='button'
                tabIndex={0}
            >
                {children}
            </div>
        </Pressable>
    );
};
