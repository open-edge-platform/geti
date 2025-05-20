// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@react-spectrum/view';

interface CornerIndicatorProps {
    isActive: boolean;
    children: JSX.Element;
}

export const CornerIndicator = ({ isActive, children }: CornerIndicatorProps): JSX.Element => {
    return (
        <View position='relative'>
            <View
                position='absolute'
                top='size-50'
                right='size-50'
                width='size-50'
                borderRadius='large'
                backgroundColor='blue-700'
                isHidden={!isActive}
            />
            {children}
        </View>
    );
};
