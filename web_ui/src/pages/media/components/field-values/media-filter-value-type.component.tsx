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

import { Item, Key, Picker, View } from '@adobe/react-spectrum';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { MEDIA_TYPE_OPTIONS } from '../../utils';

interface MediaFilterValueTypeProps {
    value: SearchRuleValue;
    isDisabled?: boolean;
    onSelectionChange: (key: SearchRuleValue) => void;
}

export const MediaFilterValueType = ({
    value = '',
    isDisabled = false,
    onSelectionChange,
}: MediaFilterValueTypeProps): JSX.Element => {
    const handleSelectionChange = (key: Key) => {
        onSelectionChange(key);
    };

    return (
        <View position='relative'>
            <Picker
                isQuiet
                isDisabled={isDisabled}
                items={MEDIA_TYPE_OPTIONS}
                id='media-filter-media-type'
                aria-label='media-filter-media-type'
                selectedKey={MEDIA_TYPE_OPTIONS.find((option) => option.text === value)?.key}
                onSelectionChange={handleSelectionChange}
            >
                {(item) => (
                    <Item key={item.key} aria-label={`option-${item.key}`}>
                        {item.text}
                    </Item>
                )}
            </Picker>
        </View>
    );
};
