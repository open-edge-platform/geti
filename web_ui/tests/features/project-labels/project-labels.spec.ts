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

import { test } from '../../fixtures/base-test';
import { SingleLabelApi } from '../../fixtures/page-objects/labels-page';
import { project as classificationProject, hierarchicalLabelsProject } from '../../mocks/classification/mocks';
import { project as detClassProject } from '../../mocks/detection-classification/mocks';
import { project as detSegProject } from '../../mocks/detection-segmentation/mocks';
import { project as segmentationProject } from '../../mocks/segmentation/mocks';
import {
    expectElementToExistDisplayMode,
    expectLabelToExist,
    expectLabelToHaveBadge,
    expectLabelToHaveConflict,
    expectLabelToHaveShortcut,
} from './expect';

const LABELS_URL =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/labels';

const labels = {
    single: {
        name: 'Chicken',
        shortcut: 'Control+1',
        shortcutText: 'CTRL+1',
        color: '#9aa219',
    },
    conflict: {
        name: 'donkey',
    },
};

const newSingleLabelApi: SingleLabelApi = {
    name: labels.single.name,
    color: labels.single.color,
    id: '6101254defba22ca453f11ca',
    group: 'species',
    is_anomalous: false,
    is_empty: false,
    hotkey: labels.single.shortcutText.toLowerCase(),
};

const speciesGroupLabel: SingleLabelApi = {
    name: 'New label',
    color: labels.single.color,
    id: '6101254defba22ca453f11c3',
    group: 'species',
    is_anomalous: false,
    is_empty: false,
    hotkey: labels.single.shortcutText.toLowerCase(),
};

const labelsFromClassification: SingleLabelApi[] | undefined = classificationProject.pipeline.tasks[1].labels || [];

const getGroupNestedLabelNames = async (page: Page, group: string) => {
    return page.getByLabel(`label item ${group}`).getByTestId('label-name').allInnerTexts();
};

test.describe('Labels editor', () => {
    test.beforeEach(async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json(segmentationProject));
        });

        await page.goto(LABELS_URL, { timeout: 20000 });
    });

    test.describe('labels creation', () => {
        test('Create single label', async ({ labelsPage, page, registerApiResponse }) => {
            await labelsPage.enableEditing();
            await expect(page.locator('role=button[name="Create label"]')).toBeDisabled();
            await labelsPage.createLabel(labels.single.name, undefined, labels.single.shortcut);
            await expectLabelToExist(page, labels.single.name);
            await expectLabelToHaveBadge(page, labels.single.name, 'New');
            await expectLabelToHaveShortcut(page, labels.single.name, 'CTRL+1');

            registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
                const projectWithLabel = {
                    ...segmentationProject,
                    pipeline: {
                        ...segmentationProject.pipeline,
                        tasks: [
                            segmentationProject.pipeline.tasks[0],
                            {
                                ...segmentationProject.pipeline.tasks[1],
                                labels: [
                                    ...(segmentationProject.pipeline.tasks[1].labels as SingleLabelApi[]),
                                    newSingleLabelApi,
                                ],
                            },
                        ],
                    },
                };
                return res(ctx.status(200), ctx.json(projectWithLabel));
            });

            await page.locator('role=button[name="Save"]').click();
            await expect(page.locator('role=alertdialog')).toBeVisible();
            await page.locator('role=button[name="Assign"]').click();

            await expectElementToExistDisplayMode(page, labels.single.name);
        });

        test('Create label with conflict', async ({ labelsPage, page }) => {
            await labelsPage.enableEditing();
            await labelsPage.createLabel(labels.conflict.name);
            await expectLabelToHaveConflict(page, labels.conflict.name);
        });
    });

    test.describe('labels editing', () => {
        const labelForEditing = (segmentationProject.pipeline.tasks[1].labels as SingleLabelApi[])[0];

        test('Edit label name', async ({ labelsPage, page }) => {
            await labelsPage.enableEditing();
            await labelsPage.editLabel(labelForEditing, 'New name');
            await expectLabelToExist(page, 'New name');
            await expectLabelToHaveBadge(page, 'New name', 'Changed');
        });

        test('Edit label shortcut', async ({ labelsPage, page }) => {
            await labelsPage.enableEditing();
            await labelsPage.editLabel(labelForEditing, undefined, undefined, 'Control+2');
            await expectLabelToExist(page, labelForEditing.name);
            await expectLabelToHaveBadge(page, labelForEditing.name, 'Changed');
            await expectLabelToHaveShortcut(page, labelForEditing.name, 'CTRL+2');
        });

        test('Edit label name to conflict', async ({ labelsPage, page }) => {
            await labelsPage.enableEditing();
            await labelsPage.editLabel(labelForEditing, labels.conflict.name);
            await expectLabelToHaveConflict(page, labels.conflict.name);
        });

        test('Edit label shortcut to conflict', async ({ labelsPage, page }) => {
            await labelsPage.enableEditing();
            await labelsPage.editLabel(labelForEditing, undefined, undefined, 'Control+6');
            await expect(page.locator('[data-testid="label-error-message-id"]')).toHaveText(
                'This hotkey is already being used'
            );
        });

        test('Color picker - project edition', async ({ labelsPage, page }) => {
            /** test plan name: color_picker_project_edition */
            await labelsPage.enableEditing();
            await labelsPage.editLabel(labelForEditing, undefined, 'c86496');

            const colorInput = page.locator(
                `#label-tree-${labelForEditing.name}-${labelForEditing.name}-color-selected-color`
            );

            const background = await colorInput.getAttribute('style');
            expect(background).toMatch('background-color: rgb(200, 100, 150)');
        });
    });

    test.describe('labels deletion', () => {
        const labelForDeleting = (segmentationProject.pipeline.tasks[1].labels as SingleLabelApi[])[0];

        test('Delete label', async ({ labelsPage, page }) => {
            await labelsPage.enableEditing();
            await labelsPage.deleteLabel(labelForDeleting);

            await expectLabelToHaveBadge(page, labelForDeleting.name, 'Removed');
        });
    });
});

test.describe('Labels editor - hierarchy classification', () => {
    test(
        'Add new hierarchy group',
        {
            annotation: {
                type: 'issue',
                description:
                    'Adding a new top level group with multiple labels to an existing hierarchical label project ' +
                    'will fail.',
            },
        },
        async ({ labelsPage, page, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
                return res(ctx.status(200), ctx.json(hierarchicalLabelsProject));
            });

            let editProjectLabelsDTO;

            registerApiResponse('EditProject', (req, res, ctx) => {
                editProjectLabelsDTO = req.body.pipeline.tasks[1].labels;

                return res(ctx.json(req.body));
            });

            const labelLz: SingleLabelApi = {
                name: 'Lz',
                color: '#fff',
                group: 'Gz',
                id: '1',
                is_anomalous: false,
                is_empty: false,
                hotkey: '',
            };
            const labelLy: SingleLabelApi = {
                name: 'Ly',
                color: '#eee',
                group: 'Gy',
                id: '12',
                is_anomalous: false,
                is_empty: false,
                hotkey: '',
            };

            await page.goto(LABELS_URL, { timeout: 20000 });

            await labelsPage.enableEditing();

            await labelsPage.createGroup('Gz');
            await labelsPage.editLabel({ name: 'Label' }, labelLz.name);

            await labelsPage.createGroupInLabel(labelLz, 'Gy');
            await labelsPage.createLabelInGroup('Gy', labelLy);

            await labelsPage.saveLabels();
            await labelsPage.assignNewLabels();

            expect(editProjectLabelsDTO).toEqual(
                expect.arrayContaining([
                    expect.objectContaining({
                        name: 'Lz',
                        group: 'Gz',
                        parent_id: null,
                        is_empty: false,
                        is_anomalous: false,
                        revisit_affected_annotations: true,
                    }),
                    expect.objectContaining({
                        name: 'Ly',
                        group: 'Gz___Gy',
                        parent_id: 'Lz',
                        is_empty: false,
                        is_anomalous: false,
                        revisit_affected_annotations: true,
                    }),
                ])
            );
        }
    );
});

test.describe('Special cases', () => {
    test.beforeEach(async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json(classificationProject));
        });

        await page.goto(LABELS_URL, { timeout: 20000 });
    });

    test.describe('Labels and groups creation', () => {
        test('Create group', async ({ labelsPage, page, registerApiResponse }) => {
            await labelsPage.enableEditing();

            await expect(page.getByRole('button', { name: 'Create group' })).toBeDisabled();

            await labelsPage.createGroup('New group');
            await expectLabelToExist(page, 'New group', true);
            await expectLabelToHaveBadge(page, 'New group', 'New');

            registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
                const projectWithGroup = {
                    ...classificationProject,
                    pipeline: {
                        ...classificationProject.pipeline,
                        tasks: [
                            classificationProject.pipeline.tasks[0],
                            {
                                ...classificationProject.pipeline.tasks[1],
                                labels: [
                                    { ...labelsFromClassification },
                                    {
                                        ...newSingleLabelApi,
                                        name: 'New group',
                                        group: 'New group',
                                    },
                                ],
                            },
                        ],
                    },
                };
                return res(ctx.status(200), ctx.json(projectWithGroup));
            });

            await page.locator('role=button[name="Save"]').click();

            await expectLabelToExist(page, 'New group', true);
        });
    });

    test('Create label in the group', async ({ labelsPage, page }) => {
        await labelsPage.enableEditing();

        await labelsPage.createLabelInGroup('species', speciesGroupLabel);
        await expectLabelToExist(page, speciesGroupLabel.name);
    });

    test('Create label inside group with conflict', async ({ labelsPage, page }) => {
        await labelsPage.enableEditing();
        await labelsPage.createLabelInGroup('species', labelsFromClassification[2]);
        await expectLabelToHaveConflict(page, 'saddled');
    });

    test('Create group inside a label', async ({ labelsPage, page }) => {
        await labelsPage.enableEditing();
        await labelsPage.createGroupInLabel(labelsFromClassification[2], 'New group');

        await expectLabelToExist(page, 'New group', true);
    });

    test('Delete group', async ({ labelsPage, page }) => {
        await labelsPage.enableEditing();
        await labelsPage.deleteLabel(labelsFromClassification[2]);

        const groupLabels = await getGroupNestedLabelNames(page, 'species');

        for (const label of groupLabels) {
            await expectLabelToHaveBadge(page, label, 'Removed');
        }
    });

    test('Cancel edition', async ({ labelsPage, page }) => {
        const groupLabelsBefore = await getGroupNestedLabelNames(page, 'species');

        await labelsPage.enableEditing();
        await labelsPage.deleteGroup('species');

        await labelsPage.cancelEditing();

        const saveButton = page.getByRole('button', { name: 'Save' });
        await expect(saveButton).toBeHidden();

        const groupLabelsAfter = await getGroupNestedLabelNames(page, 'species');

        expect(groupLabelsAfter).toHaveLength(groupLabelsBefore.length);
    });

    test('Check if default label is added in new main group', async ({ labelsPage, page }) => {
        await labelsPage.enableEditing();
        await labelsPage.createGroup('test');
        await expect(page.getByTestId('label-tree-Label-name-input')).toBeVisible();

        await page.keyboard.press('1');
        await expect(page.getByTestId('label-tree-1-name-input')).toBeVisible();
    });
});

test.describe('Task chains', () => {
    test.describe('Detection -> classification', () => {
        test.beforeEach(async ({ page, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
                return res(ctx.status(200), ctx.json(detClassProject));
            });

            await page.goto(LABELS_URL, { timeout: 20000 });
        });

        test('Check edition labels in detection -> classification', async ({ labelsPage, page }) => {
            const numberOfItemsDetectionTree = await labelsPage.getAllItemsFromTask('detection');
            await expect(numberOfItemsDetectionTree).toHaveCount(1);

            const numberOfItemsClassificationTree = await labelsPage.getAllItemsFromTask('classification');
            await expect(numberOfItemsClassificationTree).toHaveCount(14);

            await labelsPage.enableEditing();

            await labelsPage.changeNameOfNthItem('detection', 0, 'New card');
            await labelsPage.changeNameOfNthItem('classification', 1, 'A Edited');

            await labelsPage.createGroup('new group');
            await labelsPage.createLabelInGroup('new group');
            const classificationLabels = await labelsPage.getAllItemsFromTask('classification');
            await expect(classificationLabels).toHaveCount(17);

            await expect(
                (await labelsPage.getNthItemFromTask('detection', 0)).getByRole('textbox', { name: 'edited name' })
            ).toHaveValue('New card');

            await expect(
                (await labelsPage.getNthItemFromTask('classification', 1))
                    .getByRole('textbox', { name: 'edited name' })
                    .first()
            ).toHaveValue('Label 2');

            await expect(
                (await labelsPage.getNthItemFromTask('classification', 2))
                    .getByRole('textbox', { name: 'edited name' })
                    .first()
            ).toHaveValue('Label');

            const saveButton = page.getByRole('button', { name: 'Save' });
            await expect(saveButton).toBeEnabled();
            await saveButton.click();
            await expect(page.getByText('New Labels Alert: "Label", "Label 2"')).toBeVisible();

            const request = await labelsPage.getSavingLabelsRequest('61012cdb1d38a5e71ef3baf9', "Don't assign");
            const detectionLabelsRequest = request.postDataJSON().pipeline.tasks[1].labels;
            const classificationLabelsRequest = request.postDataJSON().pipeline.tasks[3].labels;

            expect(await labelsPage.getLabelsFromPayloadByName(classificationLabelsRequest, 'Label')).toStrictEqual(
                expect.objectContaining({
                    name: 'Label',
                    parent_id: detectionLabelsRequest[0].id,
                    group: 'Default group root task___new group',
                })
            );
        });

        test('Check adding labels in detection -> classification', async ({ labelsPage, page }) => {
            await labelsPage.enableEditing();
            await labelsPage.createLabelInGroup('Value');

            await expect(
                (await labelsPage.getNthItemFromTask('classification', 1))
                    .getByRole('textbox', { name: 'edited name' })
                    .first()
            ).toHaveValue('Label');

            const saveButton = page.getByRole('button', { name: 'Save' });
            await expect(saveButton).toBeEnabled();
            await saveButton.click();
            await expect(page.getByText('New Label Alert: "Label"')).toBeVisible();

            const request = await labelsPage.getSavingLabelsRequest('61012cdb1d38a5e71ef3baf9', "Don't assign");
            const detectionLabelsRequest = request.postDataJSON().pipeline.tasks[1].labels;
            const classificationLabelsRequest = request.postDataJSON().pipeline.tasks[3].labels;
            expect(await labelsPage.getLabelsFromPayloadByName(classificationLabelsRequest, 'Label')).toStrictEqual(
                expect.objectContaining({
                    name: 'Label',
                    parent_id: detectionLabelsRequest[0].id,
                    group: 'Default group root task___Value',
                })
            );
        });
    });

    test.describe('Detection -> segmentation', () => {
        test.beforeEach(async ({ page, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
                return res(ctx.status(200), ctx.json(detSegProject));
            });

            await page.goto(LABELS_URL, { timeout: 20000 });
        });

        test('Check edition labels in detection -> segmentation', async ({ labelsPage, page }) => {
            const numberOfItemsDetectionTree = await labelsPage.getAllItemsFromTask('detection');
            await expect(numberOfItemsDetectionTree).toHaveCount(1);

            const numberOfItemsSegmentationTree = await labelsPage.getAllItemsFromTask('segmentation');
            await expect(numberOfItemsSegmentationTree).toHaveCount(1);

            await labelsPage.enableEditing();

            await labelsPage.changeNameOfNthItem('detection', 0, 'Edited label detection');
            await labelsPage.changeNameOfNthItem('segmentation', 0, 'edited label segmentation');

            await labelsPage.createLabel('new label');

            const segmentationLabels = await labelsPage.getAllItemsFromTask('segmentation');
            expect(await segmentationLabels.count()).toBe(2);
            await expect(
                (await labelsPage.getNthItemFromTask('segmentation', 0))
                    .getByRole('textbox', { name: 'edited name' })
                    .first()
            ).toHaveValue('new label');

            const saveButton = page.getByRole('button', { name: 'Save' });
            await expect(saveButton).toBeEnabled();
            await saveButton.click();
            await expect(page.getByText('New Label Alert: "new label"')).toBeVisible();
        });
    });
});
