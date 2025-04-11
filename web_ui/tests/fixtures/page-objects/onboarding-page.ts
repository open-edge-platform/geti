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

import { Page } from '@playwright/test';

export class OnboardingPage {
    constructor(private page: Page) {}

    getRequestAccessButton() {
        return this.page.getByRole('button', { name: 'Request access' });
    }

    getSubmitButton() {
        return this.page.getByRole('button', { name: 'Submit' });
    }

    getRegistrationHeading() {
        return this.page.getByRole('heading', { name: /Let's complete your registration to Intel® Geti™!/ });
    }

    getRequestedAccessHeading() {
        return this.page.getByRole('heading', { name: 'Intel® Geti™ registration completed' });
    }

    getRequestAccessContent() {
        return this.page.getByRole('heading', { name: 'Thank you for your interest in Intel® Geti™.' });
    }

    async submit() {
        await this.getSubmitButton().or(this.getRequestAccessButton()).click();
    }

    async checkTermsAndConditions() {
        const termsAndConditionsCheckbox = this.page.getByRole('checkbox');

        await termsAndConditionsCheckbox.click();
    }

    async fillOrganizationName(organizationName: string) {
        const organizationNameField = this.page.getByTestId('organization-name-input');

        await organizationNameField.fill(organizationName);
    }

    getRequestAccessReasonField() {
        return this.page.getByRole('textbox', { name: /for what use case do you plan to use intel® geti™\?/i });
    }

    async fillRequestAccessReason(reason: string) {
        await this.getRequestAccessReasonField().fill(reason);
    }

    getInvalidTokenAlert() {
        return this.page.getByRole('alert').getByRole('heading', { name: 'Your invitation link has expired' });
    }
}
