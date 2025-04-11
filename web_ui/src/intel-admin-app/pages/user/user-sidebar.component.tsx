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

import { FC } from 'react';

import { paths } from '../../../core/services/routes';
import { MenuOption } from '../../../shared/components/menu-option.interface';
import { Sidebar } from '../../shared/components/sidebar/sidebar.component';
import { User } from '../users/mocked-user';

interface UserSidebarProps {
    user: User | undefined;
}

export const UserSidebar: FC<UserSidebarProps> = ({ user }) => {
    const menuOptions: MenuOption[][] = [
        [
            {
                name: 'Overview',
                ariaLabel: 'Overview',
                url: paths.intelAdmin.user.overview({ userId: user?.id ?? '' }),
            },
            {
                name: 'Memberships',
                ariaLabel: 'Memberships',
                url: paths.intelAdmin.user.memberships({ userId: user?.id ?? '' }),
            },
        ],
    ];

    return (
        <Sidebar>
            <Sidebar.Header
                name={user === undefined ? undefined : `${user.firstName} ${user.secondName}`}
                email={user?.email}
            />
            <Sidebar.Menu options={menuOptions} />
        </Sidebar>
    );
};
