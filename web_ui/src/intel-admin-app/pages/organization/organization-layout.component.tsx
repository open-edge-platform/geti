// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
