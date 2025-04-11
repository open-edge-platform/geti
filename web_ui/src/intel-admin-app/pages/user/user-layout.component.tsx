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

import { paths } from '../../../core/services/routes';
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
