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
import { MockedResponse, ResponseComposition, RestContext } from 'msw';

import { DATASET_IMPORT_TASK_TYPE_DTO } from '../../../src/core/datasets/dtos/dataset.enum';
import {
    DatasetImportLabelDTO,
    DatasetImportSupportedProjectTypeDTO,
} from '../../../src/core/datasets/dtos/dataset.interface';
import { JobState } from '../../../src/core/jobs/jobs.const';
import { OpenApiRequest } from '../../../src/core/server/types';
import { idMatchingFormat } from '../../../src/test-utils/id-utils';
import { test } from '../../fixtures/base-test';
import { setTusProgress } from '../../utils/api';
import { loadFile } from '../../utils/dom';
import { projects } from './mocks';
import { getMockedPreparingJob } from './utils';

class DatasetImportToNewProject {
    constructor(private page: Page) {}

    async openHomePage() {
        await this.page.goto('/');
    }

    async openImportModal() {
        await this.page.getByRole('button', { name: /Create project menu/i }).click();
        await this.page.getByRole('menuitem', { name: /create from dataset/i }).click();

        await expect(this.page.getByRole('heading', { name: /create project from a dataset - import/i })).toBeVisible();
    }

    async fillProjectName(projectName: string) {
        await expect(this.page.getByLabel('Project name')).toBeVisible();
        await this.page.getByRole('textbox', { name: /project name/i }).fill(projectName);
    }

    async fillProjectType(type: string) {
        await this.page.getByRole('button', { name: /show suggestions/i }).click();
        await this.page.getByRole('option', { name: type, exact: true }).click();
    }

    get projectTypeField() {
        return this.page.getByRole('combobox', { name: 'Project type Task type' });
    }

    private async clickUpload(page: Page) {
        await page.getByRole('button', { name: /upload/i }).click();
    }

    async uploadDataset(fileName: string, fileSize: number) {
        await loadFile(this.page, this.clickUpload(this.page), { name: fileName, size: fileSize });
    }

    async next() {
        await this.page.getByRole('button', { name: /next/i }).click();
    }

    get allLabels() {
        return this.page.getByLabel('select-all-labels');
    }

    get firstTaskGroup() {
        return this.page.getByTestId('tree-root-first-task-group');
    }

    get mainGroup() {
        return this.page.getByTestId('tree-root-main-group');
    }

    async selectAllLabels() {
        await this.allLabels.click();
    }

    async selectLabel(labelName: string) {
        await this.getLabel(labelName).click();
    }

    getLabel(labelName: string) {
        return this.page.getByLabel(`select-${idMatchingFormat(labelName)}-label`);
    }
}

test.describe('DatasetImportToNewProjectLabels', (): void => {
    const preparingJobId = '651bd77c1b63044e0b08b140a';
    const importingJobId = '651bd77c1b63044e0b08b140b';

    const fileSize = 256;
    const fileName = 'e2e file unique name';

    const supportedProjectTypesSingleTask = [
        {
            project_type: 'classification',
            pipeline: {
                connections: [],
                tasks: [
                    {
                        task_type: 'classification',
                        title: 'Classification 1',
                        labels: [
                            { name: 'Guitars' },

                            { name: 'Single Cut', group: 'Electric', parent: 'Guitars' },
                            { name: 'PRS Custom 22', group: 'PRS', parent: 'Single Cut' },
                            { name: 'PRS Custom 24', group: 'PRS', parent: 'Single Cut' },
                            { name: 'Gibson Les Paul Traditional', group: 'Gibson', parent: 'Single Cut' },
                            { name: 'Gibson Les Paul Studio', group: 'Gibson', parent: 'Single Cut' },
                            { name: 'Gibson Les Paul Tribute', group: 'Gibson', parent: 'Single Cut' },
                            { name: 'Fender Telecaster Nashville', group: 'Fender', parent: 'Single Cut' },
                            { name: 'Fender Jazzmaster', group: 'Fender', parent: 'Single Cut' },

                            { name: 'Double Cut', group: 'Electric', parent: 'Guitars' },
                            { name: 'Fender Stratocaster Player', group: 'Fender', parent: 'Double Cut' },
                            { name: 'Ibanez RG', group: 'Ibanez', parent: 'Double Cut' },
                            { name: 'Ibanez AZ', group: 'Ibanez', parent: 'Double Cut' },
                            { name: 'Ibanez RG421-AHM', parent: 'Ibanez RG' },
                            { name: 'Ibanez AZ2204-ICM', parent: 'Ibanez AZ' },

                            { name: 'Hollow', group: 'Acoustic', parent: 'Guitars' },
                            { name: 'PRS SE Hollowbody', group: 'PRS', parent: 'Hollow' },
                        ],
                    },
                ],
            },
        },
    ];

    test.beforeEach(async ({ registerApiResponse }): Promise<void> => {
        registerApiResponse(
            'GetAllProjectsInAWorkspace',
            (
                _: OpenApiRequest<'GetAllProjectsInAWorkspace'>,
                res: ResponseComposition<Record<string, unknown>>,
                ctx: RestContext
            ) => res(ctx.json(projects))
        );

        registerApiResponse(
            'CreateTusDatasetUpload',
            async (
                req: OpenApiRequest<'CreateTusDatasetUpload'>,
                res: ResponseComposition<Record<string, unknown>>,
                ctx: RestContext
            ): Promise<MockedResponse> =>
                res(ctx.status(200), ctx.set('Location', `http://localhost:3000/api/v1${req.path}/1234567890`))
        );

        registerApiResponse('TusDatasetUploadHead', setTusProgress(256, 256));

        registerApiResponse('PrepareDatasetForImport', (_, res, ctx) => res(ctx.json({ job_id: preparingJobId })));
        registerApiResponse('ImportProjectFromDataset', (_, res, ctx) => res(ctx.json({ job_id: importingJobId })));
    });

    test.describe('Import single task dataset', (): void => {
        test.beforeEach(async ({ registerApiResponse, page }): Promise<void> => {
            const metadata = {
                supported_project_types: supportedProjectTypesSingleTask,
                warnings: [],
                job_id: preparingJobId,
            };

            registerApiResponse('PrepareDatasetForImport', (_, res, ctx) => res(ctx.json(metadata)));
            registerApiResponse('GetJob', (_, res, ctx) =>
                res(ctx.json({ ...getMockedPreparingJob({ id: preparingJobId, state: JobState.FINISHED }), metadata }))
            );

            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await datasetImportToNewProject.openHomePage();
            await datasetImportToNewProject.openImportModal();
            await datasetImportToNewProject.uploadDataset(fileName, fileSize);
            await datasetImportToNewProject.fillProjectName('someProjectName');
            await datasetImportToNewProject.fillProjectType('Classification');
            await datasetImportToNewProject.next();
        });

        test('toggle "select all" checkbox should select/unselect all labels selection', async ({
            page,
        }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            const labels: DatasetImportLabelDTO[] = supportedProjectTypesSingleTask[0].pipeline.tasks[0].labels;
            const selection: string[] = labels.map((label: DatasetImportLabelDTO) => label.name);

            for (const labelName of selection) {
                await expect(datasetImportToNewProject.getLabel(labelName)).toBeChecked();
            }

            await datasetImportToNewProject.selectAllLabels();

            for (const labelName of selection) {
                await expect(datasetImportToNewProject.getLabel(labelName)).not.toBeChecked();
            }
        });

        test(
            'select parent should select all children in all nested levels, parent itself' +
                ' and set "parent of parent" as indeterminate since it have other children which has not been selected',
            async ({ page }): Promise<void> => {
                const datasetImportToNewProject = new DatasetImportToNewProject(page);

                await datasetImportToNewProject.selectAllLabels();
                await datasetImportToNewProject.selectLabel('Double Cut');

                const labels: DatasetImportLabelDTO[] = supportedProjectTypesSingleTask[0].pipeline.tasks[0].labels;

                const shouldBeSelected: string[] = labels
                    .filter((label: DatasetImportLabelDTO): boolean => label.parent === 'Double Cut')
                    .map((label: DatasetImportLabelDTO) => label.name);

                shouldBeSelected.push('Ibanez RG421-AHM');
                shouldBeSelected.push('Ibanez AZ2204-ICM');
                shouldBeSelected.push('Double Cut');

                const shouldNotBeSelected: string[] = labels
                    .filter((label: DatasetImportLabelDTO): boolean => label.parent === 'Single Cut')
                    .map((label: DatasetImportLabelDTO) => label.name);

                shouldNotBeSelected.push('PRS SE Hollowbody');
                shouldNotBeSelected.push('Hollow');
                shouldNotBeSelected.push('Single Cut');

                // Check that "parent of parent" has an indeterminate state
                expect(
                    await datasetImportToNewProject
                        .getLabel('Guitars')
                        .evaluate((e: HTMLInputElement) => e.indeterminate)
                ).toBe(true);

                for (const labelName of shouldBeSelected) {
                    await expect(datasetImportToNewProject.getLabel(labelName)).toBeChecked();
                }

                for (const labelName of shouldNotBeSelected) {
                    await expect(datasetImportToNewProject.getLabel(labelName)).not.toBeChecked();
                }
            }
        );

        test(
            'select child should select itself and set "parent" and "parent of parent" as indeterminate' +
                ' since they have other children which has not been selected',
            async ({ page }): Promise<void> => {
                const datasetImportToNewProject = new DatasetImportToNewProject(page);

                await datasetImportToNewProject.selectAllLabels();
                await datasetImportToNewProject.selectLabel('PRS Custom 24');

                // Check that "self" has a checked state
                await expect(datasetImportToNewProject.getLabel('PRS Custom 24')).toBeChecked();

                // Check that "parent" has an indeterminate state
                expect(
                    await datasetImportToNewProject
                        .getLabel('Single Cut')
                        .evaluate((e: HTMLInputElement) => e.indeterminate)
                ).toBe(true);

                // Check that "parent of parent" has an indeterminate state
                expect(
                    await datasetImportToNewProject
                        .getLabel('Guitars')
                        .evaluate((e: HTMLInputElement) => e.indeterminate)
                ).toBe(true);
            }
        );

        test('unselect child should not affect parent and other children after it was selected by parent', async ({
            page,
        }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await datasetImportToNewProject.selectAllLabels();
            await datasetImportToNewProject.selectLabel('Double Cut');

            const labels: DatasetImportLabelDTO[] = supportedProjectTypesSingleTask[0].pipeline.tasks[0].labels;

            const shouldBeSelected: string[] = labels
                .filter((label: DatasetImportLabelDTO): boolean => label.parent === 'Double Cut')
                .map((label: DatasetImportLabelDTO) => label.name);

            // Check that "parent" is checked
            await expect(datasetImportToNewProject.getLabel('Double Cut')).toBeChecked();

            // Check that root "parent" has an indeterminate state
            expect(
                await datasetImportToNewProject.getLabel('Guitars').evaluate((e: HTMLInputElement) => e.indeterminate)
            ).toBe(true);

            // Check that "select all" has an indeterminate state
            expect(await datasetImportToNewProject.allLabels.evaluate((e: HTMLInputElement) => e.indeterminate)).toBe(
                true
            );

            await expect(datasetImportToNewProject.getLabel('Ibanez AZ2204-ICM')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('Ibanez RG421-AHM')).toBeChecked();
            for (const labelName of shouldBeSelected) {
                await expect(datasetImportToNewProject.getLabel(labelName)).toBeChecked();
            }

            await datasetImportToNewProject.selectLabel('Ibanez AZ2204-ICM');

            // Check that "parent" has an indeterminate state since not all the children selected now
            expect(
                await datasetImportToNewProject
                    .getLabel('Double Cut')
                    .evaluate((e: HTMLInputElement) => e.indeterminate)
            ).toBe(true);

            // Check that root "parent" still has an indeterminate state since not all the children selected
            expect(
                await datasetImportToNewProject.getLabel('Guitars').evaluate((e: HTMLInputElement) => e.indeterminate)
            ).toBe(true);

            // Check that "select all" still has an indeterminate state since not all the children selected
            expect(await datasetImportToNewProject.allLabels.evaluate((e: HTMLInputElement) => e.indeterminate)).toBe(
                true
            );

            await expect(datasetImportToNewProject.getLabel('Ibanez AZ2204-ICM')).not.toBeChecked();
            await expect(datasetImportToNewProject.getLabel('Ibanez RG421-AHM')).toBeChecked();
            for (const labelName of shouldBeSelected) {
                await expect(datasetImportToNewProject.getLabel(labelName)).toBeChecked();
            }

            await datasetImportToNewProject.selectLabel('Ibanez RG421-AHM');

            // Check that "parent" has an indeterminate state since not all the children selected now
            expect(
                await datasetImportToNewProject
                    .getLabel('Double Cut')
                    .evaluate((e: HTMLInputElement) => e.indeterminate)
            ).toBe(true);

            // Check that root "parent" still has an indeterminate state since not all the children selected
            expect(
                await datasetImportToNewProject.getLabel('Guitars').evaluate((e: HTMLInputElement) => e.indeterminate)
            ).toBe(true);

            // Check that "select all" still has an indeterminate state since not all the children selected
            expect(await datasetImportToNewProject.allLabels.evaluate((e: HTMLInputElement) => e.indeterminate)).toBe(
                true
            );

            await expect(datasetImportToNewProject.getLabel('Ibanez AZ2204-ICM')).not.toBeChecked();
            await expect(datasetImportToNewProject.getLabel('Ibanez RG421-AHM')).not.toBeChecked();
            for (const labelName of shouldBeSelected) {
                await expect(datasetImportToNewProject.getLabel(labelName)).toBeChecked();
            }
        });

        test('select child should select parent if there is no other children are present', async ({
            page,
        }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await datasetImportToNewProject.selectAllLabels();
            await datasetImportToNewProject.selectLabel('PRS SE Hollowbody');

            await expect(datasetImportToNewProject.getLabel('PRS SE Hollowbody')).toBeChecked();

            await expect(datasetImportToNewProject.getLabel('Hollow')).toBeChecked();
        });
    });

    test.describe('Import task chained dataset', (): void => {
        const supportedProjectTypesTaskChained: DatasetImportSupportedProjectTypeDTO[] = [
            {
                project_type: 'detection_segmentation',
                pipeline: {
                    connections: [
                        {
                            from: 'dataset_0',
                            to: 'detection_1',
                        },
                        {
                            from: 'detection_1',
                            to: 'crop_2',
                        },
                        {
                            from: 'crop_2',
                            to: 'segmentation_3',
                        },
                    ],
                    tasks: [
                        {
                            title: 'dataset_0',
                            task_type: DATASET_IMPORT_TASK_TYPE_DTO.DATASET,
                            labels: [],
                        },
                        {
                            title: 'detection_1',
                            task_type: DATASET_IMPORT_TASK_TYPE_DTO.DETECTION,
                            labels: [
                                {
                                    name: 'det',
                                    group: 'Detection labels',
                                },
                            ],
                        },
                        {
                            title: 'crop_2',
                            task_type: DATASET_IMPORT_TASK_TYPE_DTO.CROP,
                            labels: [],
                        },
                        {
                            title: 'segmentation_3',
                            task_type: DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION,
                            labels: [
                                {
                                    name: 'label1',
                                    group: 'Detection labels___Segmentation labels',
                                },
                                {
                                    name: 'label2',
                                    group: 'Detection labels___Segmentation labels',
                                },
                            ],
                        },
                    ],
                },
            },
        ];

        test.beforeEach(async ({ registerApiResponse, page }): Promise<void> => {
            const metadata = {
                supported_project_types: supportedProjectTypesTaskChained,
                warnings: [],
                job_id: preparingJobId,
            };

            registerApiResponse('PrepareDatasetForImport', (_, res, ctx) => res(ctx.json(metadata)));
            registerApiResponse('GetJob', (_, res, ctx) =>
                res(ctx.json({ ...getMockedPreparingJob({ id: preparingJobId, state: JobState.FINISHED }), metadata }))
            );

            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await datasetImportToNewProject.openHomePage();
            await datasetImportToNewProject.openImportModal();
            await datasetImportToNewProject.uploadDataset(fileName, fileSize);
            await datasetImportToNewProject.fillProjectName('someProjectName');
            await datasetImportToNewProject.fillProjectType('Detection > Segmentation');
            await datasetImportToNewProject.next();
        });

        test('additional section for detection label should be shown', async ({ page }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await expect(datasetImportToNewProject.firstTaskGroup).toBeVisible();
            await expect(datasetImportToNewProject.mainGroup).toBeVisible();
        });

        test('detection label should be selected and disabled by default', async ({ page }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            await expect(datasetImportToNewProject.getLabel('label1')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label1')).toBeEnabled();

            await expect(datasetImportToNewProject.getLabel('label2')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).toBeEnabled();
        });

        test('detection label should disabled and click on it should not toggle the selection', async ({
            page,
        }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            // Force click on "disabled" element
            await datasetImportToNewProject.getLabel('det').evaluate((node: HTMLElement): void => node.click());

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();
        });

        test('detection label should not be affected on toggling "Select all" checkbox', async ({
            page,
        }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            await expect(datasetImportToNewProject.allLabels).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label1')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).toBeChecked();

            await datasetImportToNewProject.selectAllLabels();

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            await expect(datasetImportToNewProject.allLabels).not.toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label1')).not.toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).not.toBeChecked();

            await datasetImportToNewProject.selectAllLabels();

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            await expect(datasetImportToNewProject.allLabels).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label1')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).toBeChecked();
        });

        test('detection label should not be affected on toggling selection of the other labels', async ({
            page,
        }): Promise<void> => {
            const datasetImportToNewProject = new DatasetImportToNewProject(page);

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            await expect(datasetImportToNewProject.allLabels).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label1')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).toBeChecked();

            await datasetImportToNewProject.selectLabel('label1');

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            expect(await datasetImportToNewProject.allLabels.evaluate((e: HTMLInputElement) => e.indeterminate)).toBe(
                true
            );
            await expect(datasetImportToNewProject.getLabel('label1')).not.toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).toBeChecked();

            await datasetImportToNewProject.selectLabel('label2');

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            await expect(datasetImportToNewProject.allLabels).not.toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label1')).not.toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).not.toBeChecked();

            await datasetImportToNewProject.selectLabel('label1');

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            expect(await datasetImportToNewProject.allLabels.evaluate((e: HTMLInputElement) => e.indeterminate)).toBe(
                true
            );
            await expect(datasetImportToNewProject.getLabel('label1')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).not.toBeChecked();

            await datasetImportToNewProject.selectLabel('label2');

            await expect(datasetImportToNewProject.getLabel('det')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('det')).toBeDisabled();

            await expect(datasetImportToNewProject.allLabels).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label1')).toBeChecked();
            await expect(datasetImportToNewProject.getLabel('label2')).toBeChecked();
        });
    });

    test.describe('Project type selection and label selection', (): void => {
        test(
            'Project type should be automatically selected and labels mapped ' + 'when there is only one project type',
            async ({ page, registerApiResponse }) => {
                const metadata = {
                    supported_project_types: supportedProjectTypesSingleTask,
                    warnings: [],
                    job_id: preparingJobId,
                };

                registerApiResponse('PrepareDatasetForImport', (_, res, ctx) => res(ctx.json(metadata)));
                registerApiResponse('GetJob', (_, res, ctx) =>
                    res(
                        ctx.json({
                            ...getMockedPreparingJob({ id: preparingJobId, state: JobState.FINISHED }),
                            metadata,
                        })
                    )
                );

                const datasetImportToNewProject = new DatasetImportToNewProject(page);

                await datasetImportToNewProject.openHomePage();
                await datasetImportToNewProject.openImportModal();
                await datasetImportToNewProject.uploadDataset(fileName, fileSize);
                await datasetImportToNewProject.fillProjectName('Test project');

                await expect(datasetImportToNewProject.projectTypeField).toHaveValue('Classification');

                await datasetImportToNewProject.next();

                const labels: DatasetImportLabelDTO[] = supportedProjectTypesSingleTask[0].pipeline.tasks[0].labels;

                for (const label of labels) {
                    await expect(datasetImportToNewProject.getLabel(label.name)).toBeChecked();
                }
            }
        );

        test(
            'Project type should not be automatically selected when there are at least two project types, ' +
                'selecting  and labels mapped when there is only one task type',
            async ({ page, registerApiResponse }) => {
                const supportedManyProjectTypes = [
                    {
                        project_type: 'detection',
                        pipeline: {
                            connections: [
                                {
                                    from: 'Dataset',
                                    to: 'Detection',
                                },
                            ],
                            tasks: [
                                {
                                    title: 'Dataset',
                                    task_type: 'dataset',
                                    labels: [],
                                },
                                {
                                    title: 'Detection',
                                    task_type: 'detection',
                                    labels: [
                                        {
                                            name: 'Brick2x6',
                                            group: 'Detection labels',
                                        },
                                        {
                                            name: 'brick 2x4',
                                            group: 'Detection labels',
                                        },
                                        {
                                            name: 'other',
                                            group: 'Detection labels',
                                        },
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        project_type: 'detection_oriented',
                        pipeline: {
                            connections: [
                                {
                                    from: 'Dataset',
                                    to: 'Detection Oriented',
                                },
                            ],
                            tasks: [
                                {
                                    title: 'Dataset',
                                    task_type: 'dataset',
                                    labels: [],
                                },
                                {
                                    title: 'Detection Oriented',
                                    task_type: 'rotated_detection',
                                    labels: [
                                        {
                                            name: 'Brick2x6',
                                            group: 'Detection Oriented Task Labels',
                                        },
                                        {
                                            name: 'brick 2x4',
                                            group: 'Detection Oriented Task Labels',
                                        },
                                        {
                                            name: 'other',
                                            group: 'Detection Oriented Task Labels',
                                        },
                                    ],
                                },
                            ],
                        },
                    },
                ];

                const metadata = {
                    supported_project_types: supportedManyProjectTypes,
                    warnings: [],
                    job_id: preparingJobId,
                };

                registerApiResponse('PrepareDatasetForImport', (_, res, ctx) => res(ctx.json(metadata)));
                registerApiResponse('GetJob', (_, res, ctx) =>
                    res(
                        ctx.json({
                            ...getMockedPreparingJob({ id: preparingJobId, state: JobState.FINISHED }),
                            metadata,
                        })
                    )
                );

                const datasetImportToNewProject = new DatasetImportToNewProject(page);

                await datasetImportToNewProject.openHomePage();
                await datasetImportToNewProject.openImportModal();
                await datasetImportToNewProject.uploadDataset(fileName, fileSize);
                await datasetImportToNewProject.fillProjectName('Test project');

                await expect(datasetImportToNewProject.projectTypeField).toHaveValue('');

                await datasetImportToNewProject.fillProjectType('Detection');

                await datasetImportToNewProject.next();

                const detectionLabels = supportedManyProjectTypes[0].pipeline.tasks.filter(
                    ({ task_type }) => task_type === DATASET_IMPORT_TASK_TYPE_DTO.DETECTION
                )[0].labels;

                for (const label of detectionLabels) {
                    await expect(datasetImportToNewProject.getLabel(label.name)).toBeChecked();
                }
            }
        );
    });
});
