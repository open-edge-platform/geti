// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
