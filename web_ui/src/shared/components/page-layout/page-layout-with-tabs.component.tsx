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

import { Key, ReactNode } from 'react';

import { Divider, Flex, Item, TabList, TabPanels, Tabs, Text, View } from '@adobe/react-spectrum';
import { DimensionValue } from '@react-types/shared/src/dna';
import { Responsive } from '@react-types/shared/src/style';

import { TabItem } from '../tabs/tabs.interface';

import classes from './page-layout.module.scss';

interface PageLayoutProps {
    activeTab: string;
    tabs: TabItem[];
    tabsLabel: string;
    tabsTopMargin?: Responsive<DimensionValue>;
    tabContentTopMargin?: Responsive<DimensionValue>;
    actionButton?: ReactNode;
    onSelectionChange: (key: Key) => void;
}

export const PageLayoutWithTabs = ({
    tabs,
    tabsLabel,
    activeTab,
    actionButton,
    tabsTopMargin,
    onSelectionChange,
    tabContentTopMargin,
}: PageLayoutProps): JSX.Element => {
    return (
        <Flex id={`page-layout-id`} direction='column' height='100%'>
            <Tabs
                isQuiet
                aria-label={tabsLabel}
                items={tabs}
                width={'100%'}
                height={'100%'}
                onSelectionChange={onSelectionChange}
                selectedKey={activeTab}
                marginTop={tabsTopMargin}
            >
                <Flex alignItems={'center'} justifyContent={'space-between'} width={'100%'}>
                    <TabList width={'100%'}>
                        {(item: TabItem) => (
                            <Item key={item.key as string} textValue={item.name as string}>
                                <Text id={item.id}>{item.name}</Text>
                            </Item>
                        )}
                    </TabList>
                    <View>{actionButton}</View>
                </Flex>
                <Divider size='S' />
                <Flex position='relative' flex={1} direction='column' minHeight={0} marginTop={tabContentTopMargin}>
                    <TabPanels height={'100%'} minHeight={0} UNSAFE_className={classes.pageLayoutTabs}>
                        {(item: TabItem) => (
                            <Item key={item.key as string} textValue={item.name as string}>
                                {item.children}
                            </Item>
                        )}
                    </TabPanels>
                </Flex>
            </Tabs>
        </Flex>
    );
};
