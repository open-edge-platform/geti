// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import React, { CSSProperties, forwardRef } from 'react';

import { SpectrumActionButtonProps, Text } from '@adobe/react-spectrum';
import { useFocusableRef, useStyleProps } from '@react-spectrum/utils';
import { FocusableRef } from '@react-types/shared';
import { FocusRing, useButton } from 'react-aria';

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
