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

import { JobState } from '../../../src/core/jobs/jobs.const';
import { annotatorTest as test } from '../../fixtures/annotator-test';
import { expect } from '../../fixtures/base-test';
import { setTusProgress } from '../../utils/api';
import { loadFile } from '../../utils/dom';
import { getMockedExistingProjectPreparingJob } from '../project-dataset/utils';

test.describe('LabelSearch usage', () => {
    test.fixme('annotator screen detection -> classification', async ({ page, registerApiExample }) => {
        registerApiExample('GetProjectInfo', 'Detection classification response');

        const taskId = '62946c61003ddb3967f1474f';
        await page.goto(
            // eslint-disable-next-line max-len
            `http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/62946c61003ddb3967f14750/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa?task-id=${taskId}`
        );

        const canvas = page.getByLabel('Annotator canvas');

        await canvas.getByText('Select label').dblclick();

        await page.getByRole('listitem', { name: 'label item Spades' }).click();

        await expect(canvas).toBeVisible();
    });

    test('annotator screen detection -> segmentation', async ({ page, registerApiResponse, registerApiExample }) => {
        registerApiExample('GetProjectInfo', 'Detection Segmentation response');
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(
                ctx.json({
                    annotations: [
                        {
                            id: 'input-annotation',
                            labels: [
                                {
                                    color: '#26518eff',
                                    id: '60db493ed20945a0046f56c6',
                                    name: 'test',
                                    probability: 1,
                                    source: {
                                        user_id: 'default_user',
                                        model_id: '61387685df33ae8280c347b2',
                                        model_storage_id: '62387685df33ae8280c63a34',
                                    },
                                },
                            ],
                            labels_to_revisit: ['61387685df33ae8280c33d9d', '61387685df33ae8280c33d9e'],
                            modified: '2021-09-08T12:43:22.265000+00:00',
                            shape: { type: 'RECTANGLE', x: 100, y: 100, width: 300, height: 300 },
                        },
                        {
                            id: 'output-annotation',
                            labels: [
                                {
                                    color: '#26518eff',
                                    id: '60db493ed20945a0046f56c7',
                                    name: 'test',
                                    probability: 1,
                                    source: {
                                        user_id: 'default_user',
                                        model_id: '61387685df33ae8280c347b2',
                                        model_storage_id: '62387685df33ae8280c63a34',
                                    },
                                },
                            ],
                            labels_to_revisit: ['61387685df33ae8280c33d9d', '61387685df33ae8280c33d9e'],
                            modified: '2021-09-08T12:43:22.265000+00:00',
                            shape: { type: 'RECTANGLE', x: 150, y: 150, width: 100, height: 100 },
                        },
                    ],
                    id: '6138afea3b7b11505c43f2c0',
                    kind: 'annotation',
                    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
                    modified: '2021-09-08T12:43:22.290000+00:00',
                    labels_to_revisit_full_scene: ['61387685df33ae8280c33d9d'],
                    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
                })
            )
        );

        const taskId = '60db493fd20945a0046f56d6';
        await page.goto(
            // eslint-disable-next-line max-len
            `http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/62946c61003ddb3967f14750/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa?task-id=${taskId}`
        );

        await expect(page.getByRole('list', { name: 'Annotations list' })).toBeVisible();
        const list = page.getByRole('list', { name: 'Annotations list' });
        const annotationItem = list.getByRole('listitem', { name: /annotation/i });
        await annotationItem.scrollIntoViewIfNeeded();
        await annotationItem.getByRole('list').dblclick();

        const rectangle = page.getByRole('listitem', { name: 'label item rectangle' });
        await rectangle.click();

        const canvas = page.getByLabel('Annotator canvas');
        await expect(canvas).toBeVisible();

        await canvas.getByText('Select label').click();

        await page.getByRole('listitem', { name: /rectangle/ }).click();

        await expect(canvas.getByText('rectangle')).toBeVisible();
        await expect(list.getByText('rectangle')).toBeVisible();
    });

    test.describe('annotator screen', () => {
        test.beforeEach(async ({ page, registerApiExample }) => {
            registerApiExample('GetProjectInfo', 'Detection classification response');

            await page.goto(
                // eslint-disable-next-line max-len
                'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/62946c61003ddb3967f14750/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa'
            );
        });

        const targetLabel = 'Hearts';
        const parentLabel = 'Card';

        test('More labels shortcut', async ({ page }) => {
            const labelName = 'Seven';
            await page.getByRole('button', { name: /More/ }).click();
            await page.getByLabel('Select label').fill(labelName);

            const seven = page.getByRole('listitem', { name: /Seven/ });
            await seven.hover();
            await seven.getByRole('button', { name: /pin/ }).click();

            const labelShortcuts = page.getByRole('list', { name: 'Label shortcuts' });
            await expect(labelShortcuts.getByRole('button', { name: 'Seven' })).toBeVisible();
        });

        test('annotation list bulk action', async ({ page }) => {
            await expect(page.getByRole('list', { name: 'Annotations list' })).toBeVisible();

            await page.getByRole('checkbox', { name: /annotations selected/i }).check();

            await page
                .getByRole('button', {
                    name: /assign label to selected annotations/i,
                })
                .click();

            const resultsContainer = page.getByLabel('Label search results');
            await resultsContainer.getByRole('listitem', { name: targetLabel }).click();

            const list = page.getByRole('list', { name: 'Annotations list' });
            const annotationItem = list.getByRole('listitem').nth(0);

            await expect(annotationItem).toHaveText(`${parentLabel} ${targetLabel}`);
        });

        test('Default label combobox', async ({ page }) => {
            await page.getByLabel('Close hierarchical label view').click();

            const combobox = page.getByRole('textbox', {
                name: /select default label/i,
            });

            await combobox.focus();

            const resultsContainer = page.getByLabel('Label search results');
            await resultsContainer.getByRole('listitem', { name: targetLabel }).click();

            const view = page.getByTestId('default-label-id');
            await expect(view.getByText(new RegExp(targetLabel))).toBeVisible();
        });

        test('annotation list item', async ({ page }) => {
            const list = page.getByRole('list', { name: 'Annotations list' });
            const annotationItem = list.getByRole('listitem');

            await annotationItem.getByText('Select label').click();

            const resultsContainer = page.getByLabel('Label search results');
            await resultsContainer.getByRole('listitem', { name: targetLabel }).click();
        });

        test('label filter', async ({ page }) => {
            await page.getByRole('button', { name: /filter media/i }).click();

            const button = page.getByRole('button', {
                name: /media\-filter\-field/,
            });
            await button.click();

            await page.getByRole('menuitemradio', { name: 'Label' }).click();

            await page
                .getByRole('button', {
                    name: /media\-filter\-operator/,
                })
                .click();
            await page.getByRole('menuitemradio', { name: 'In', exact: true }).click();

            const textbox = page.getByRole('textbox', {
                name: 'media-filter-label',
            });
            await textbox.click();

            const label = page.getByLabel(`label item ${targetLabel}`);
            await label.click();

            await expect(textbox).toHaveValue(new RegExp(targetLabel));
        });

        test('annotation label search', async ({ page, selectionTool }) => {
            await selectionTool.selectTool();
            const labelsSelection = page.getByTestId('transform-zoom-canvas').getByLabel('labels');

            await labelsSelection.click();

            await expect(page.getByLabel('Label search results')).toBeVisible();

            const classificationGroupToggleButton = page.getByLabel(
                'toggleable chevron Default group root task___Suit'
            );

            const labels = ['Hearts', 'Diamonds', 'Clubs', 'Spades'];

            for (const label of labels) {
                await expect(page.getByLabel(`label item ${label}`)).toBeVisible();
            }

            await classificationGroupToggleButton.click();

            for (const label of labels) {
                await expect(page.getByLabel(`label item ${label}`)).toBeHidden();
            }
        });
    });

    test('dataset import', async ({ page, registerApiExample, registerApiResponse }) => {
        registerApiExample('GetProjectInfo', 'Classification response');

        const preparingJobId = '651bd77c1b63044e0b08b140a';
        const uploadId = '123-321-213';

        registerApiResponse('CreateTusDatasetUpload', async (req, res, ctx) => {
            return res(ctx.status(200), ctx.set('Location', `http://localhost:3000/api/v1${req.path}/${uploadId}`));
        });

        const metadata = {
            labels: ['lion', 'tortoise', 'pony', 'dog', 'cat'],
            warnings: [
                {
                    type: 'warning',
                    name: 'Missing expected annotation type for classification domain',
                    description: 'Image contains no global label',
                    affected_images: 5,
                },
            ],
            job_id: preparingJobId,
        };
        registerApiResponse('PrepareDatasetForImportToProject', (_, res, ctx) => {
            return res(ctx.json(metadata));
        });

        registerApiResponse('GetJob', (_, res, ctx) => {
            return res(
                ctx.json({
                    ...getMockedExistingProjectPreparingJob({ id: preparingJobId, state: JobState.FINISHED }),
                    metadata,
                })
            );
        });

        const fileSize = 256;
        registerApiResponse('TusDatasetUploadHead', setTusProgress(fileSize, fileSize));

        await page.goto(
            // eslint-disable-next-line max-len
            'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/media'
        );

        await page
            .getByRole('tab', { name: 'Open dataset menu' })
            .filter({ hasText: 'Example classification project' })
            .click();

        await page.getByRole('menuitem', { name: 'Import dataset' }).click();

        const fileName = 'e2e file unique name';
        await loadFile(page, page.getByRole('button', { name: /upload/i }).click(), {
            name: fileName,
            size: fileSize,
        });

        const textboxes = page.getByRole('textbox', { name: /label/ });
        await expect(textboxes).toHaveCount(5);

        await textboxes.nth(1).selectText();
        await page.getByRole('listitem', { name: /horse/, includeHidden: true }).click();
        await expect(page.getByRole('listitem', { name: /horse/, includeHidden: true })).toBeHidden();

        await textboxes.nth(3).selectText();
        await page.getByRole('listitem', { name: /donkey/, includeHidden: true }).click();
        await expect(page.getByRole('listitem', { name: /donkey/, includeHidden: true })).toBeHidden();

        await page.getByRole('button', { name: 'Import' }).click();
    });
});
