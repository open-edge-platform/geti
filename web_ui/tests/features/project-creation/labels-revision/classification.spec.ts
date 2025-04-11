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

import { expect } from '@playwright/test';

import { testWithOpenApi } from '../fixtures';

testWithOpenApi('Create hierarchical classification project with duplicated names', async ({ createProjectPage }) => {
    //test_hierarchical_labels_identical_names

    const labels: Record<string, string[]> = {
        group1: ['label1', 'label1'],
    };

    // labels:
    //     group1
    //         label1
    //             group1
    //         label1
    await createProjectPage.selectClassificationHierarchicalAndGoToLabels('Playwright duplicated names');
    await createProjectPage.createLabelHierarchy(labels);
    expect(await (await createProjectPage.getLabelsValidationErrors()).count()).toBe(1);
    await expect(await createProjectPage.getLabelError('label1')).toBeVisible();
    await createProjectPage.addChildGroup('label1', 'group1');
    expect(await (await createProjectPage.getLabelsValidationErrors()).count()).toBe(2);
    await expect(await createProjectPage.getLabelError('group1', 1)).toBeVisible();

    await createProjectPage.removeItem('label1', 'label');
    expect(await (await createProjectPage.getLabelsValidationErrors()).count()).toBe(0);

    // labels:
    //     group1
    //         label1
    //             group2
    //     group1
    //         label1
    await createProjectPage.addChildGroup('label1', 'group2');
    await createProjectPage.addGroup('test group');
    await createProjectPage.changeGroupName('test group', 'group1');
    await createProjectPage.changeLabelName('Label', 'label1');

    expect(await (await createProjectPage.getLabelsValidationErrors()).count()).toBe(2);

    await createProjectPage.removeItem('group1', 'group');
    expect(await (await createProjectPage.getLabelsValidationErrors()).count()).toBe(0);
    // labels:
    //     group1
    //         label1
    //             group2
    //     group3
    //         label4
    //             group4
    //                 label1
    await createProjectPage.addGroup('test group');
    await createProjectPage.changeGroupName('test group', 'group3');
    await createProjectPage.changeLabelName('Label', 'label4');
    await createProjectPage.addChildGroup('label4', 'group4');
    await createProjectPage.addChildLabel('group4', 'label1');

    expect(await (await createProjectPage.getLabelsValidationErrors()).count()).toBe(1);
});

testWithOpenApi(
    'Create hierarchical classification project with duplicated names deeper in the tree',
    async ({ createProjectPage, page }) => {
        await createProjectPage.selectClassificationHierarchicalAndGoToLabels('Playwright duplicated names scenario 2');

        // label tree:
        //     groupA
        //       label 1
        //     groupB
        //        label 2
        //     groupC
        //        label 3
        //     groupD <--- Deleting this one should remove all errors down the tree
        //       label 1 (duplicated)
        //              groupD (duplicated)
        await createProjectPage.addGroup('A');
        await createProjectPage.changeLabelName('Label', 'Label 1');

        await expect(page.locator('#label-tree-view-container').locator('li')).toHaveCount(2);

        await createProjectPage.addGroup('B');
        await createProjectPage.changeLabelName('Label', 'Label 2');

        await expect(page.locator('#label-tree-view-container').locator('li')).toHaveCount(4);

        await createProjectPage.addGroup('C');
        await createProjectPage.changeLabelName('Label', 'Label 3');

        await expect(page.locator('#label-tree-view-container').locator('li')).toHaveCount(6);

        await createProjectPage.addGroup('D');
        await createProjectPage.changeLabelName('Label', 'Label 1');
        await createProjectPage.addChildGroup('Label 1', 'D');

        await expect(page.getByText("Label 'Label 1' already exists")).toBeVisible();
        await expect(page.getByText("Group 'D' already exists")).toBeVisible();

        await expect(page.getByRole('button', { name: 'Create', exact: true })).toBeDisabled();

        await createProjectPage.removeItem('D', 'group');
        await expect(page.getByRole('button', { name: 'Create', exact: true })).toBeEnabled();

        await expect(await createProjectPage.getLabelsValidationErrors()).toHaveCount(0);
    }
);
