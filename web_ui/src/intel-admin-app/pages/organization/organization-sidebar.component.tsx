// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MenuOption } from '@shared/components/menu-option.interface';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../../../core/services/routes';
import { Sidebar } from '../../shared/components/sidebar/sidebar.component';
import { useOrganization } from './hooks/organization.hook';

export const OrganizationSidebar = (): JSX.Element => {
    const { organization } = useOrganization();
    const { FEATURE_FLAG_ORG_QUOTAS, FEATURE_FLAG_MANAGE_USERS } = useFeatureFlags();

    const menuOptions: MenuOption[][] = [
        [
            {
                id: 'overview',
                name: 'Overview',
                ariaLabel: 'Overview',
                url: paths.intelAdmin.organization.overview({ organizationId: organization?.id ?? '' }),
            },
            {
                id: 'credits',
                name: 'Credits',
                ariaLabel: 'Credits',
                url: paths.intelAdmin.organization.creditAccounts({ organizationId: organization?.id ?? '' }),
            },
            {
                id: 'service_limits',
                name: 'Service limits',
                ariaLabel: 'Service limits',
                url: paths.intelAdmin.organization.serviceLimits({ organizationId: organization?.id ?? '' }),
                isHidden: !FEATURE_FLAG_ORG_QUOTAS,
            },
            {
                id: 'organization-users',
                name: 'Users',
                ariaLabel: 'Users',
                url: paths.intelAdmin.organization.users({ organizationId: organization?.id ?? '' }),
                isHidden: !FEATURE_FLAG_MANAGE_USERS,
            },
        ],
    ];

    return (
        <Sidebar>
            <Sidebar.Header name={organization === undefined ? undefined : organization.name} />
            <Sidebar.Menu options={menuOptions} id='organization' />
        </Sidebar>
    );
};
