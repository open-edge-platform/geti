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

import { Flex, Item, TabList, TabPanels } from '@adobe/react-spectrum';
import { Tabs } from '@react-spectrum/tabs';

import { TabItem, TabsProps } from '../../tabs/tabs.interface';

import classes from './selectable-customized-tabs.module.scss';

export const SelectableCustomizedTabs = (props: TabsProps): JSX.Element => {
    return (
        <Tabs {...props} UNSAFE_className={classes.customizedTabs}>
            <TabList minWidth={{ base: 'auto', L: '24rem' }}>
                {(item: TabItem) => (
                    <Item key={item.key} textValue={item.key}>
                        <Flex
                            justifyContent={'space-between'}
                            alignItems={'center'}
                            gap={'size-50'}
                            id={item.id}
                            data-testid={item.id}
                        >
                            <>{item.name}</>
                        </Flex>
                    </Item>
                )}
            </TabList>
            <TabPanels
                minHeight={0}
                position={'relative'}
                UNSAFE_style={{ overflowY: 'auto' }}
                marginStart={{ base: 'size-150', L: 'size-250' }}
                marginEnd={{ base: 'size-150', L: '0' }}
            >
                {(item: TabItem) => <Item key={item.key}>{item.children}</Item>}
            </TabPanels>
        </Tabs>
    );
};
