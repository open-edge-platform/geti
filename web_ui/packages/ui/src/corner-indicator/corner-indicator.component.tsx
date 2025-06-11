// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { View } from '@adobe/react-spectrum';

interface CornerIndicatorProps {
    isActive: boolean;
    children: JSX.Element;
    position?: 'left' | 'right';
    testId?: string;
    containerStyle?: CSSProperties;
}

export const CornerIndicator = ({
    isActive,
    children,
    position = 'right',
    testId,
    containerStyle,
}: CornerIndicatorProps): JSX.Element => {
    const positionAttribute = {
        left: {
            left: 'calc(-1 * size-100)',
        },
        right: {
            right: 'size-50',
            top: 'size-50',
        },
    };

    return (
        <View position='relative' UNSAFE_style={containerStyle} data-testid={testId}>
            <View
                position='absolute'
                {...positionAttribute[position]}
                width='size-50'
                height='size-50'
                borderRadius='large'
                backgroundColor='blue-700'
                isHidden={!isActive}
            />
            {children}
        </View>
    );
};
