// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatus } from '../../../core/organizations/organizations.interface';
import { getItemActions, OrganizationsMenuItems } from './utils';

describe('Test organization action items', () => {
    it('Actions when status is INVITED', () => {
        expect(getItemActions(AccountStatus.INVITED)).toStrictEqual([OrganizationsMenuItems.DELETE]);
    });

    it('Actions when status is ACTIVATED', () => {
        expect(getItemActions(AccountStatus.ACTIVATED)).toStrictEqual([
            OrganizationsMenuItems.SUSPEND,
            OrganizationsMenuItems.DELETE,
        ]);
    });

    it('Actions when status is SUSPENDED', () => {
        expect(getItemActions(AccountStatus.SUSPENDED)).toStrictEqual([
            OrganizationsMenuItems.ACTIVATE,
            OrganizationsMenuItems.DELETE,
        ]);
    });

    it('Actions when status is DELETED', () => {
        expect(getItemActions(AccountStatus.DELETED)).toStrictEqual([]);
    });
});
