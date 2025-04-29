// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
