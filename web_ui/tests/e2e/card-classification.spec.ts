// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import fs from 'fs';

import { resolveDatasetPath } from '../utils/dataset';
import { expectProjectToHaveLabels, expectProjectToHaveType } from './../features/project-creation/expect';
import { expect } from './../fixtures/base-test';
import { test } from './fixtures';
import { loadCardAnnotations } from './utils';

// This test can either be run where we only classify the suit of cards,
// or we can run it where we add a new values group and annotate each
// card separately
const CHANGE_PROJECT_LABELS_AFTER_UPLOAD = true as boolean;

test('Card classification', async ({
    createProjectPage,
    page,
    mediaPage,
    labelShortcutsPage,
    labelsPage,
    projectPage,
    annotatorPage,
}) => {
    await page.goto('/');

    const cards = loadCardAnnotations();

    const classificationLabels: Record<string, string[]> = {
        Suit: ['Hearts', 'Diamonds', 'Spades', 'Clubs'],
    };
    if (CHANGE_PROJECT_LABELS_AFTER_UPLOAD === false) {
        classificationLabels['Value'] = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
    }
    await test.step('create project', async () => {
        await page.getByRole('button', { name: /create new/i }).click();

        const cardProjectPage = await createProjectPage.classificationHierarchical(
            `Card suit classification${CHANGE_PROJECT_LABELS_AFTER_UPLOAD ? ' with revisit' : ''}`,
            classificationLabels
        );

        const labels = Object.keys(classificationLabels).flatMap((group) => classificationLabels[group]);

        await expectProjectToHaveType(cardProjectPage, 'Classification');
        await expectProjectToHaveLabels(cardProjectPage, labels);
    });

    let totalFiles = 0;

    await test.step('importing media', async () => {
        await projectPage.goToDatasetPage();

        const bucket = await mediaPage.getBucket();

        for (const suit of classificationLabels['Suit']) {
            const path = resolveDatasetPath(`cards/${suit.toLocaleLowerCase()}`);
            const files = fs.readdirSync(path).map((filename) => resolveDatasetPath(path, filename));
            await bucket.uploadFiles(files, [suit]);

            totalFiles += files.length;

            await expect(async () => {
                const message = page.getByText(new RegExp(`Uploaded ${totalFiles} of ${totalFiles} files`));
                await expect(message).toBeVisible();
            }).toPass({
                timeout: 1000 * 60 * 10,
            });
        }
    });

    await test.step('add new labels', async () => {
        if (CHANGE_PROJECT_LABELS_AFTER_UPLOAD === false) {
            return;
        }
        await projectPage.goToLabelsPage();
        await labelsPage.enableEditing();

        const group = 'Value';
        await labelsPage.createGroup(group);

        const groupList = page.getByRole('listitem', { name: `label item ${group}` });
        const groupListItem = groupList.getByLabel(`${group} group`);
        const editBoxes = groupList.getByRole('textbox', { name: /edited name/i });

        const labels = { Value: ['7', '8', '9', '10', 'J', 'Q', 'K', 'A'] };
        for (let labelIdx = 0; labelIdx < labels[group].length; labelIdx++) {
            const label = labels[group][labelIdx];

            await groupListItem.hover();
            const currentLabel = editBoxes.nth(labelIdx);
            if (!(await currentLabel.isVisible())) {
                await groupList.getByRole('button', { name: 'add child label button' }).click();
            }

            await editBoxes.nth(0).fill(label);
        }

        const saveButtonLocator = page.getByRole('button', { name: /save/i });
        await saveButtonLocator.click();

        await page.getByRole('button', { name: 'Assign', exact: true }).click();
        await expect(page.getByText(/Labels have been changed/)).toBeVisible();
    });

    classificationLabels['Value'] = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

    await test.step('annotate cards', async () => {
        await page.getByRole('link', { name: /datasets/i }).click();

        const bucket = await mediaPage.getBucket();
        await bucket
            .getBucketLocator()
            .getByRole('img', {
                name: /img/i,
            })
            .nth(0)
            .dblclick();

        await expect(page.getByRole('list', { name: /labels/i })).toBeVisible();

        await labelShortcutsPage.openLabelShortcutsMenu();
        await labelShortcutsPage.pinLabel('8');
        await labelShortcutsPage.pinLabel('9');
        await labelShortcutsPage.pinLabel('10');
        await labelShortcutsPage.pinLabel('J');
        await labelShortcutsPage.pinLabel('Q');
        await labelShortcutsPage.pinLabel('K');
        await labelShortcutsPage.pinLabel('A');
        await labelShortcutsPage.closeLabelShortcutsMenu();

        for (let idx = 0; idx < totalFiles; idx++) {
            const filename = await annotatorPage.selectedMediaFilename();
            const card = cards.find((image) => image.name === filename);

            const labelList = page.getByRole('list', { name: /labels/i });
            for (const annotation of card?.annotations ?? []) {
                for (const label of annotation.labels) {
                    if (await labelList.getByText(label).isVisible()) {
                        continue;
                    }

                    const labelBtn = await labelShortcutsPage.getPinnedLabelLocator(label);
                    await labelBtn.click();
                }
            }

            const url = page.url();
            const nextItem = page.getByRole('button', { name: /next media item/i });

            if (await nextItem.isEnabled()) {
                if (CHANGE_PROJECT_LABELS_AFTER_UPLOAD === false) {
                    await nextItem.click();
                }

                const submitButton = page.getByRole('button', { name: /submit/i });
                if (await submitButton.isEnabled()) {
                    await submitButton.click();
                }
                await expect(page).not.toHaveURL(url);
            } else {
                const submitButton = page.getByRole('button', { name: /submit/i });
                if (await submitButton.isEnabled()) {
                    await submitButton.click();
                }

                break;
            }
        }
    });

    console.info('Finished');
});
