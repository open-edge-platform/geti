// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
                height='size-50'
                borderRadius='large'
                backgroundColor='blue-700'
                isHidden={!isActive}
            />
            {children}
        </View>
    );
};
