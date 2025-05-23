// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';

import { DetailsContentLayout } from '../../shared/components/details-content-layout/details-content-layout.component';
import { MOCKED_USERS } from '../users/mocked-user';
import { UserSidebar } from './user-sidebar.component';

const [user] = MOCKED_USERS;

export const UserLayout = () => {
    return (
        <DetailsContentLayout
            breadcrumbs={[
                {
                    id: 'home',
                    breadcrumb: 'Home',
                    href: paths.intelAdmin.index({}),
                },
                {
                    id: 'users-id',
                    breadcrumb: 'Users',
                    href: paths.intelAdmin.users({}),
                },
                {
                    id: `user-${user.id}-id`,
                    breadcrumb: `${user.firstName} ${user.secondName}`,
                },
            ]}
            sidebar={<UserSidebar user={user} />}
        />
    );
};
