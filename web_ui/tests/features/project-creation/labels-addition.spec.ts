// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { testWithOpenApi as test } from './fixtures';

test.describe('Project creation - labels addition', () => {
    test('Color picker - project creation', async ({ createProjectPage, page }) => {
        /** test plan name: color_picker_project_creation */

        await createProjectPage.selectClassificationSingleLabelAndGoToLabels('Classification Single Labels');

        const colorButton = page.getByRole('button', { name: 'Color picker button' });
        await colorButton.click();
        await createProjectPage.changeColorInEdition('5ed6d3');

        await page.getByRole('textbox', { name: /project label name input/i }).click();
        await createProjectPage.addLabel('test');

        await createProjectPage.checkColor('test', 'test', 'rgb(94, 214, 211)');

        await page.getByTestId('label-tree-test-test-color-button').click();

        await createProjectPage.changeColorInEdition('ff0000');
        await expect(page.getByTestId('popover')).toBeHidden({ timeout: 10000 });

        await createProjectPage.checkColor('test', 'test', 'rgb(255, 0, 0)');

        await createProjectPage.addLabel('test2');
        await page.getByRole('button', { name: 'Create', exact: true }).click();
    });

    test('Main group with default label - empty tree - hierarchical classification', async ({
        createProjectPage,
        page,
    }) => {
        /** test plan name: new_hierarchical_main_label_group_empty_tree */

        await createProjectPage.selectClassificationHierarchicalAndGoToLabels('Classification hierarchical');

        await createProjectPage.addGroup('test');

        await expect(page.getByRole('textbox', { name: 'edited name' })).toHaveValue('Label');

        await page.keyboard.press('1');
        await expect(page.getByRole('textbox', { name: 'edited name' })).toHaveValue('1');
    });

    test('Main group with default label - not empty tree - hierarchical classification', async ({
        createProjectPage,
        page,
    }) => {
        /** test plan name: new_hierarchical_main_label_group_not_empty_tree */

        await createProjectPage.selectClassificationHierarchicalAndGoToLabels('Classification hierarchical');

        await createProjectPage.addGroup('test');

        await createProjectPage.addChildLabel('test');
        await createProjectPage.addChildLabel('test');

        await createProjectPage.addGroup('test2');

        await expect(page.getByRole('textbox', { name: 'edited name' }).nth(0)).toHaveValue('Label 4');
    });

    test('Child group - hierarchical classification', async ({ createProjectPage, page }) => {
        /** test plan name: new_hierarchical_child_label_group */

        await createProjectPage.selectClassificationHierarchicalAndGoToLabels('Classification hierarchical');

        await createProjectPage.addGroup('test');
        await createProjectPage.addChildGroup('Label', 'test');

        await expect(page.locator('#label-tree-view-container').locator('li')).toHaveCount(3);
    });
});
