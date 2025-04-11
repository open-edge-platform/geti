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

import { useStyleProps } from '@react-spectrum/utils';
import { View } from '@react-spectrum/view';
import { StyleProps } from '@react-types/shared';
import { ColorValue, DimensionValue } from '@react-types/shared/src/dna';

export interface ThinProgressBarProps extends StyleProps {
    progress: number;
    completed?: boolean;
    color?: ColorValue;
    customColor?: string;
    trackColor?: ColorValue;
    size?: DimensionValue;
    id?: string;
}

export const ThinProgressBar = ({
    progress = 0,
    completed = false,
    size = 'size-50',
    color = 'blue-400',
    customColor = '',
    trackColor = 'gray-400',
    id,
    ...otherProps
}: ThinProgressBarProps): JSX.Element => {
    const { styleProps } = useStyleProps(otherProps);

    return (
        <View
            id={id}
            height={size}
            backgroundColor={trackColor}
            width='100%'
            borderRadius='small'
            UNSAFE_style={{ ...styleProps.style }}
        >
            <View
                height={size}
                backgroundColor={customColor ? undefined : color}
                width={completed ? '100%' : `${progress}%`}
                borderRadius='regular'
                UNSAFE_style={{ backgroundColor: customColor }}
                data-testid='thin-progress-bar'
            />
        </View>
    );
};
