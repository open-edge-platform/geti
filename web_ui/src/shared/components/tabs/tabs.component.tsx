// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Item, Tabs as SpectrumTabs, TabList, TabPanels } from '@geti/ui';

import { TabItem, TabsProps } from './tabs.interface';

import classes from './tabs.module.scss';

export const Tabs = ({
    tabPanelsClassName,
    tabStyles = {},
    hideSelectionBar = false,
    ...props
}: TabsProps): JSX.Element => {
    const panelOverflowY = props.panelOverflowY ?? 'auto';

    return (
        <SpectrumTabs {...props}>
            <TabList UNSAFE_className={hideSelectionBar ? classes.hideSelectionBar : ''}>
                {(item: TabItem) => (
                    <Item key={item.key} textValue={item.key}>
                        <Flex direction={'row'} alignItems={'center'} gap={'size-50'} id={item.id}>
                            <>{item.name}</>
                        </Flex>
                    </Item>
                )}
            </TabList>

            <TabPanels
                UNSAFE_className={[classes.tabPanels, tabPanelsClassName ?? ''].join(' ')}
                UNSAFE_style={{ ...tabStyles, overflowY: panelOverflowY }}
            >
                {(item: TabItem) => <Item key={item.key}>{item.children}</Item>}
            </TabPanels>
        </SpectrumTabs>
    );
};
