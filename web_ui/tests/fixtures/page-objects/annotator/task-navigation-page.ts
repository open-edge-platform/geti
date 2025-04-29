// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

export class TaskNavigationPage {
    constructor(private page: Page) {}

    async selectTaskMode(task: 'All Tasks' | 'Detection' | 'Classification' | 'Segmentation') {
        await this.page
            .getByRole('navigation', { name: 'navigation-breadcrumbs' })
            .getByRole('button', { name: task })
            .click();
    }
}
