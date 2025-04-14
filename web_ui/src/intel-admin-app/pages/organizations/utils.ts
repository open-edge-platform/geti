// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatus } from '../../../core/organizations/organizations.interface';

export enum OrganizationsMenuItems {
    SUSPEND = 'Suspend',
    DELETE = 'Delete',
    ACTIVATE = 'Activate',
}

export const getItemActions = (status: AccountStatus) => {
    switch (status) {
        case AccountStatus.ACTIVATED:
            return [OrganizationsMenuItems.SUSPEND, OrganizationsMenuItems.DELETE];

        case AccountStatus.SUSPENDED:
            return [OrganizationsMenuItems.ACTIVATE, OrganizationsMenuItems.DELETE];

        case AccountStatus.INVITED:
            return [OrganizationsMenuItems.DELETE];

        case AccountStatus.REQUESTED_ACCESS:
            return [OrganizationsMenuItems.ACTIVATE, OrganizationsMenuItems.DELETE];

        default:
            return [];
    }
};
