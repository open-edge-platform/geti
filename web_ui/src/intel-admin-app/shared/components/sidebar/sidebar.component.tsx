// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { View } from '@adobe/react-spectrum';

import { SidebarMenu } from '../../../../shared/components/sidebar-menu/sidebar-menu.component';
import { SidebarHeader } from './sidebar-header.component';

interface SidebarProps {
    children: ReactNode;
}

export const Sidebar = ({ children }: SidebarProps) => {
    return (
        <View backgroundColor={'gray-75'} height={'100%'}>
            {children}
        </View>
    );
};

Sidebar.Header = SidebarHeader;
Sidebar.Menu = SidebarMenu;
