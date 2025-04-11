// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { ActionElement } from '../../../../../shared/components/action-element/action-element.component';

interface VideoItemDataIndicatorProps {
    children: ReactNode;
    tooltip?: string;
    id: string;
}

export const VideoItemDataIndicator = ({ children, tooltip, id }: VideoItemDataIndicatorProps): JSX.Element => {
    return (
        <View
            id={id}
            data-testid={id}
            paddingX={'size-50'}
            borderColor={'gray-400'}
            borderWidth={'thin'}
            borderRadius={'regular'}
        >
            <TooltipTrigger placement={'bottom'}>
                <ActionElement>{children}</ActionElement>
                <Tooltip>{tooltip}</Tooltip>
            </TooltipTrigger>
        </View>
    );
};
