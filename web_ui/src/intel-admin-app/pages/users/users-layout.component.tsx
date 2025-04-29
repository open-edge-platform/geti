// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '../../../core/services/routes';
import { ContentLayout } from '../../shared/components/content-layout/content-layout.component';
import { Users } from './users.component';

export const UsersLayout = () => {
    return (
        <ContentLayout
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
            ]}
        >
            <Users />
        </ContentLayout>
    );
};
