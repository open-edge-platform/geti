// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { RunTestDialogPage } from './run-test-dialog-page';
import { ProjectTestsPage } from './tests-page';
import { TrainModelDialogPage } from './train-model-dialog-page';

export class ProjectModelsPage {
    constructor(private page: Page) {}

    async goToModel(architectureName: string, version: string) {
        const listItem = this.page.getByLabel(`${architectureName} version ${version}`);
        await listItem.click();

        return new ProjectModelPage(this.page);
    }

    async openTestDialog(architectureName: string, version: string) {
        const listItem = this.page.getByLabel(`${architectureName} version ${version}`);

        const menu = listItem.getByRole('button', { name: /model action menu/i });
        await menu.click();
        await this.page.getByRole('menuitem', { name: /run tests/i }).click();

        return new RunTestDialogPage(this.page);
    }

    async openTrainDialog() {
        const trainButton = this.page.getByTestId('train-new-model-button-id');
        await trainButton.click();

        return new TrainModelDialogPage(this.page);
    }

    async seeTestProgress() {
        await this.page.getByRole('button', { name: /see progress/i }).click();

        return new ProjectTestsPage(this.page);
    }
}

class ProjectModelPage {
    constructor(private page: Page) {}

    async openTestDialog(optimization: string) {
        const row = this.page.getByRole('row', { name: new RegExp(optimization, 'i') });
        const menu = row.getByRole('button', { name: /model action menu/i });

        await menu.click();

        await this.page.getByRole('menuitem', { name: 'Run tests' }).click();

        return new RunTestDialogPage(this.page);
    }
}
