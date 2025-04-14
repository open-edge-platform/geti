// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
