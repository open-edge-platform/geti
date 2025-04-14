// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { CreateProjectPage } from './create-project-page';

export class WorkspacesPage {
    constructor(private page: Page) {}

    async createProject() {
        await this.page.getByRole('button', { name: 'Create new project' }).nth(0).click();

        return new CreateProjectPage(this.page);
    }
}
