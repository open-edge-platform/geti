// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '../../../core/services/routes';
import { Skeleton } from '../../../shared/components/skeleton/skeleton.component';
import { DetailsContentLayout } from '../../shared/components/details-content-layout/details-content-layout.component';
import { useOrganization } from './hooks/organization.hook';
import { OrganizationSidebar } from './organization-sidebar.component';

import classes from './organization.module.scss';

export const OrganizationLayout = (): JSX.Element => {
    const { organization } = useOrganization();

    return (
        <>
            <DetailsContentLayout
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
                    {
                        id: 'organization-id',
                        breadcrumb: organization ? (
                            organization.name
                        ) : (
                            <Skeleton
                                width={'size-1600'}
                                height={'size-300'}
                                UNSAFE_className={classes.breadcrumbsSkeleton}
                            />
                        ),
                    },
                ]}
                sidebar={<OrganizationSidebar />}
            />
        </>
    );
};
