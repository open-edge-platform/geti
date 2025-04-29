// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
