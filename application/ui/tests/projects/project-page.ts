// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Page } from '@playwright/test';

import { paths } from '../../src/constants/paths';

type ProjectFormOptions = {
    name: string;
    task: string;
    classificationType?: 'Single-label' | 'Multi-label';
    labelNames: string[];
};

// How long to wait for a project card marked as "Active" before concluding no pipeline is running.
const ACTIVE_PIPELINE_TIMEOUT = 1000 * 10;

export class ProjectPage {
    constructor(private page: Page) {}

    async gotoList() {
        await this.page.goto(paths.project.index({}));
    }

    async gotoCreate() {
        await this.page.goto(paths.project.new({}));
    }

    getCreateNewProjectButton() {
        return this.page.getByRole('button', { name: 'Create new project' });
    }

    getCreateProjectButton() {
        return this.page.getByRole('button', { name: /Create project/ });
    }

    async setProjectName(name: string) {
        await this.page.getByRole('textbox', { name: 'Project name input' }).fill(name);
    }

    async selectTask(task: string) {
        await this.page.getByLabel(task, { exact: true }).click();
    }

    async selectClassificationType(type: 'Single-label' | 'Multi-label') {
        await this.page.getByRole('radio', { name: type }).click();
    }

    async addLabel(labelName: string) {
        await this.page.getByRole('textbox', { name: 'Create label input' }).fill(labelName);
        await this.page.getByRole('button', { name: /Create label/ }).click();
    }

    async fillProjectForm({ name, task, classificationType, labelNames }: ProjectFormOptions) {
        await this.setProjectName(name);
        await this.selectTask(task);

        if (classificationType !== undefined) {
            await this.selectClassificationType(classificationType);
        }

        for (const labelName of labelNames) {
            await this.addLabel(labelName);
        }
    }

    async openProjectMenu(projectName: string) {
        await this.getProjectCard(projectName).getByLabel('open project options').click();
    }

    /** The backend allows a single running pipeline, so one left running elsewhere blocks enabling another. */
    async disableActivePipeline() {
        await this.gotoList();

        const activeProject = this.getProjectCards().filter({ hasText: 'Active' }).first();

        try {
            await activeProject.waitFor({ timeout: ACTIVE_PIPELINE_TIMEOUT });
        } catch {
            return;
        }

        await activeProject.getByLabel('open project options').click();
        await this.page.getByRole('menuitem', { name: 'Disable pipeline' }).click();

        await this.page
            .getByLabel('toast')
            .filter({ hasText: 'Pipeline disabled successfully' })
            .waitFor({ timeout: ACTIVE_PIPELINE_TIMEOUT });
        await activeProject.waitFor({ state: 'hidden', timeout: ACTIVE_PIPELINE_TIMEOUT });
    }

    async clickDeleteMenuAction() {
        await this.page.getByText(/Delete/).click();
    }

    async confirmDeleteProject() {
        await this.page.getByRole('button', { name: /Delete/ }).click();
    }

    getProjectCard(projectName: string) {
        return this.page.getByLabel(`Project: ${projectName}`);
    }

    getProjectCards() {
        return this.page.getByLabel(/^Project: /);
    }
}
