// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
