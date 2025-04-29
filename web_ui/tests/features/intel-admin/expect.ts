// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
