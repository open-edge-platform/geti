// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '../../../core/services/routes';
import { ContentLayout } from '../../shared/components/content-layout/content-layout.component';
import { Organizations } from './organizations.component';

export const OrganizationsLayout = (): JSX.Element => {
    return (
        <ContentLayout
            breadcrumbs={[
                {
                    id: 'home',
                    breadcrumb: 'Home',
                    href: paths.intelAdmin.index({}),
                },
                {
                    id: 'organizations-id',
                    breadcrumb: 'Organizations',
                    href: paths.intelAdmin.organizations({}),
                },
            ]}
        >
            <Organizations />
        </ContentLayout>
    );
};
