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
import { usePress } from 'react-aria';

interface CPSelectableItemProps<T extends string | number> {
    id: string;
    value: T;
    selectedOption: T;
    handleOptionChange: (selectedOption: T) => void;
}

export const CPSelectableItem = <T extends string | number>(props: CPSelectableItemProps<T>): JSX.Element => {
    const { id, value, handleOptionChange, selectedOption } = props;

    const { pressProps } = usePress({
        onPress: () => {
            handleOptionChange(value);
        },
    });

    return (
        <div {...pressProps}>
            <View
                id={id}
                borderColor={'gray-400'}
                borderRadius={'small'}
                borderWidth={'thin'}
                paddingX={'size-150'}
                paddingY={'size-65'}
                backgroundColor={selectedOption === value ? 'gray-200' : 'gray-50'}
                UNSAFE_style={{ cursor: 'pointer' }}
            >
                {value}
            </View>
        </div>
    );
};
