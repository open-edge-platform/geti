// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { ProjectPage } from '../../fixtures/page-objects/project-page';

export const expectProjectToHaveType = async (projectPage: ProjectPage, projectType: string) => {
    expect(await projectPage.getProjectType()).toEqual(projectType);
};

export const expectProjectToHaveLabels = async (projectPage: ProjectPage, labels: string[]) => {
    await projectPage.goToLabelsPage();

    for (const label of labels) {
        await expect(projectPage.label(label)).toBeVisible();
    }
};

export const expectProjectHasHierarchicalLabels = async (page: Page, labels: Record<string, string[]>) => {
    for (const group of Object.keys(labels)) {
        const groupList = page.getByRole('listitem', { name: new RegExp(group) });
        const labelListItems = await groupList.getByRole('listitem').all();
        expect(labelListItems).toHaveLength(labels[group].length);

        for (let labelIdx = 0; labelIdx < labels[group].length; labelIdx++) {
            const label = labels[group][labelIdx];

            await expect(groupList.getByRole('listitem', { name: new RegExp(label) })).toBeVisible();
        }
    }
};
