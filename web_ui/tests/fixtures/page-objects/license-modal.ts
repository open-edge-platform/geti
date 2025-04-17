// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

export class LicenseModalPage {
    constructor(private page: Page) {}

    getDialog() {
        return this.page.getByRole('dialog', { name: /LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE AGREEMENT/i });
    }

    getLicenseAcceptButton() {
        return this.getDialog().getByRole('button', { name: 'Accept' });
    }

    getLicenseCloseButton() {
        return this.getDialog().getByRole('button', { name: 'Close' });
    }

    async acceptLicense() {
        return this.getDialog().getByRole('button', { name: 'Accept' }).click();
    }
}
