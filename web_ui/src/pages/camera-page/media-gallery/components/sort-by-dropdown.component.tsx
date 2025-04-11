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

import { Key } from 'react';

import { Flex, Item, Picker, Text } from '@adobe/react-spectrum';

import { SortingOptions } from '../../util';

interface SortByDropdownProps {
    onSelect: (key: SortingOptions) => void;
}

export const SortByDropdown = ({ onSelect }: SortByDropdownProps): JSX.Element => {
    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            <Text UNSAFE_style={{ fontWeight: 'bold' }}>Sort by: </Text>

            <Picker
                isQuiet
                maxWidth={'size-2000'}
                aria-label='sorting options'
                defaultSelectedKey={SortingOptions.MOST_RECENT}
                onSelectionChange={(key: Key) => onSelect(key as SortingOptions)}
            >
                <Item key={SortingOptions.MOST_RECENT}>Most Recent</Item>
                <Item key={SortingOptions.LABEL_NAME_A_Z}>Label Name (A-Z)</Item>
                <Item key={SortingOptions.LABEL_NAME_Z_A}>Label Name (Z-A)</Item>
                {/* TODO: put back with video implementation
                <Item key={SortingOptions.VIDEOS}>Videos</Item>
                <Item key={SortingOptions.PHOTOS}>Photos</Item> */}
            </Picker>
        </Flex>
    );
};
