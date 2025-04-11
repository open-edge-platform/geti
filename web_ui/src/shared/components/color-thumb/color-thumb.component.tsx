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

import { View, ViewProps } from '@react-spectrum/view';
import { StyleProps } from '@react-types/shared';

export interface ColorThumbProps extends StyleProps {
    color: string;
    id: string;
    size?: number;
    borderRadius?: ViewProps<5>['borderRadius'];
}

export const ColorThumb = ({ color, id, size = 10, ...viewProps }: ColorThumbProps): JSX.Element => {
    return (
        <View
            id={id}
            width={size}
            minWidth={size}
            height={size}
            borderRadius={'small'}
            UNSAFE_style={{
                backgroundColor: color,
            }}
            {...viewProps}
        />
    );
};
