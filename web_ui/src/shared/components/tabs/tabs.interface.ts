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

import { ComponentProps, CSSProperties, ReactNode } from 'react';

import { TabPanels } from '@adobe/react-spectrum';
import { SpectrumTabsProps } from '@react-types/tabs';

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
