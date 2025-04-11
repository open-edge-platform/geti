// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
