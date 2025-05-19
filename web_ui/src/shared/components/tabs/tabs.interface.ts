// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, CSSProperties, ReactNode } from 'react';

import { SpectrumTabsProps, TabPanels } from '@geti/ui';

interface PanelOverflowY {
    panelOverflowY?: 'visible' | 'hidden' | 'clip' | 'scroll' | 'auto';
}

export interface TabItem {
    id: string;
    key: string;
    name: ReactNode;
    children: ReactNode;
    isLearningParametersTab?: boolean;
}

export interface TabsProps extends Omit<SpectrumTabsProps<TabItem>, 'children'>, PanelOverflowY {
    tabStyles?: CSSProperties;
    hideSelectionBar?: boolean;
    tabPanelsClassName?: ComponentProps<typeof TabPanels>['UNSAFE_className'];
}
