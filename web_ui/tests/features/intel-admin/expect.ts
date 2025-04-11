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

import { expect, Page } from '@playwright/test';

import { OrganizationDTO } from '../../../src/core/organizations/dtos/organizations.interface';
import { ORGANIZATION_STATUS_MAPPER } from '../../../src/core/organizations/services/utils';

export const expectToHaveNRows = async (page: Page, numberOfRows: number) => {
    return expect(
        page.getByRole('row').filter({ hasNot: page.getByText(/MEMBERSHIP SINCE/) }) // filter out table header
    ).toHaveCount(numberOfRows);
};

interface UserRow {
    name: string;
    admin: string;
    status: string;
}
export const expectTableContainsUserRow = async (page: Page, { name, admin, status }: UserRow) => {
    await expect(page.getByRole('row', { name })).toBeVisible();
    await expect(page.getByRole('row', { name }).getByText(admin)).toBeVisible();
    await expect(page.getByRole('row', { name }).getByText(status)).toBeVisible();
};

export const expectToHaveTableContent = async (page: Page, organizations: OrganizationDTO[]) => {
    for (const organization of organizations) {
        await expectTableContainsUserRow(page, {
            name: organization.name,
            admin: `${organization.admins[0].firstName} ${organization.admins[0].lastName}`,
            status: ORGANIZATION_STATUS_MAPPER[organization.status],
        });
    }

    await expectToHaveNRows(page, organizations.length);
};
