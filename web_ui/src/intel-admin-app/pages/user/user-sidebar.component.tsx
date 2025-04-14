// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
