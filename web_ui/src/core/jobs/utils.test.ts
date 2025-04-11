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

import { getMockedGeneralJobDTO, getMockedJob } from '../../test-utils/mocked-items-factory/mocked-jobs';
import { JobType } from './jobs.const';
import { getJobCountEntity, getJobEntity, isJobDataset, isJobOptimization, isJobTest, isJobTrain } from './utils';

describe('jobs utils', () => {
    it('isJobDataset', () => {
        expect(isJobDataset(getMockedJob({ type: JobType.TRAIN }))).toBe(false);
        expect(isJobDataset(getMockedJob({ type: JobType.OPTIMIZATION_POT }))).toBe(false);

        expect(isJobDataset(getMockedJob({ type: JobType.EXPORT_DATASET }))).toBe(true);
        expect(isJobDataset(getMockedJob({ type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT }))).toBe(true);
        expect(isJobDataset(getMockedJob({ type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT }))).toBe(true);
        expect(isJobDataset(getMockedJob({ type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT }))).toBe(true);
        expect(isJobDataset(getMockedJob({ type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT }))).toBe(true);
        expect(isJobDataset(getMockedJob({ type: JobType.IMPORT_PROJECT }))).toBe(true);
        expect(isJobDataset(getMockedJob({ type: JobType.EXPORT_PROJECT }))).toBe(true);
    });

    it('isJobTest', () => {
        expect(isJobTest(getMockedJob({ type: JobType.TEST }))).toBe(true);
        expect(isJobTest(getMockedJob({ type: JobType.TRAIN }))).toBe(false);
    });

    it('isJobOptimization', () => {
        expect(isJobOptimization(getMockedJob({ type: JobType.TRAIN }))).toBe(false);
        expect(isJobOptimization(getMockedJob({ type: JobType.OPTIMIZATION_POT }))).toBe(true);
    });

    it('isJobTrain', () => {
        expect(isJobTrain(getMockedJob({ type: JobType.OPTIMIZATION_POT }))).toBe(false);
        expect(isJobTrain(getMockedJob({ type: JobType.TRAIN }))).toBe(true);
    });

    it('getJobCountEntity', () => {
        const data = {
            n_running_jobs: 1,
            n_finished_jobs: 2,
            n_scheduled_jobs: 3,
            n_cancelled_jobs: 4,
            n_failed_jobs: 5,
        };
        expect(getJobCountEntity(data)).toEqual({
            numberOfFailedJobs: data.n_failed_jobs,
            numberOfRunningJobs: data.n_running_jobs,
            numberOfFinishedJobs: data.n_finished_jobs,
            numberOfCancelledJobs: data.n_cancelled_jobs,
            numberOfScheduledJobs: data.n_scheduled_jobs,
        });
    });

    describe('getJobEntity', () => {
        const generalJobDTO = getMockedGeneralJobDTO({});

        it('test job', () => {
            const project = { id: 'project-id', name: 'project-name' };
            const datasets = [{ id: 'dataset-id', name: 'dataset-name' }];
            const model = {
                id: 'model-id',
                architecture: 'architecture-test',
                template_id: '123',
                has_xai_head: false,
                optimization_type: '',
                precision: ['1'],
            };

            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.TEST,
                    metadata: {
                        test: {
                            datasets,
                            model,
                        },
                        task: { task_id: 'task_id-test' },
                        project,
                    },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.TEST,
                    metadata: {
                        project,
                        task: { taskId: 'task_id-test' },
                        test: {
                            datasets,
                            model: {
                                id: model.id,
                                precision: model.precision,
                                modelTemplateId: model.template_id,
                                hasExplainableAI: model.has_xai_head,
                                architectureName: model.architecture,
                                optimizationType: model.optimization_type,
                            },
                        },
                    },
                })
            );
        });

        it('optimization job', () => {
            const project = { id: 'project-id', name: 'project-name' };
            const task = {
                task_id: 'task_id',
                model_architecture: 'model_architecture',
                model_template_id: 'model_template_id',
                dataset_storage_id: 'dataset_storage_id',
            };

            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.OPTIMIZATION_POT,
                    metadata: {
                        task,
                        project,
                        base_model_id: 'base_model_id',
                        model_storage_id: 'model_storage_id',
                        optimization_type: 'optimization_type',
                    },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.OPTIMIZATION_POT,
                    metadata: {
                        project,
                        baseModelId: 'base_model_id',
                        modelStorageId: 'model_storage_id',
                        optimizationType: 'optimization_type',
                        optimizedModelId: undefined,
                        task: {
                            taskId: task.task_id,
                            modelTemplateId: task.model_template_id,
                            modelArchitecture: task.model_architecture,
                        },
                    },
                })
            );
        });

        it('export dataset job', () => {
            const downloadUrl = 'download_url_test';

            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.EXPORT_DATASET,
                    metadata: {
                        download_url: downloadUrl,
                        project: {
                            id: 'project-id',
                            name: 'some-project',
                        },
                    },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.EXPORT_DATASET,
                    metadata: {
                        downloadUrl,
                        project: {
                            id: 'project-id',
                            name: 'some-project',
                        },
                    },
                })
            );
        });

        it('prepare import to new project job', () => {
            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT,
                    metadata: {
                        warnings: [],
                        supported_project_types: [],
                    },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT,
                    metadata: { supportedProjectTypes: [], warnings: [] },
                })
            );
        });

        it('perform import to new project job', () => {
            const project_id = 'project_id_test';
            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT,
                    metadata: {
                        project_id,
                    },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT,
                    metadata: { projectId: project_id },
                })
            );
        });

        it('prepare import to existing project job', () => {
            const labels = ['label-1', 'label-2'];
            const project = { id: 'test-id', name: 'project-test-name' };

            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT,
                    metadata: {
                        labels,
                        warnings: [],
                        project,
                    },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT,
                    metadata: { labels, warnings: [], project },
                })
            );
        });

        it('perform import to existing project job', () => {
            const project = { id: 'test-id', name: 'project-test-name' };
            const dataset = {
                id: 'dataset-id',
                name: 'dataset-name',
                creation_time: 'dataset-creation_time',
                use_for_training: false,
            };
            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT,
                    metadata: { dataset, project },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT,
                    metadata: {
                        dataset: {
                            id: dataset.id,
                            name: dataset.name,
                            creationTime: dataset.creation_time,
                            useForTraining: dataset.use_for_training,
                        },
                        project,
                    },
                })
            );
        });

        it('train job', () => {
            const project = { id: 'project-id', name: 'project-name' };
            const trainedModel = { model_id: 'model-id' };
            const task = {
                task_id: 'task_id',
                model_architecture: 'model_architecture',
                model_template_id: 'model_template_id',
                dataset_storage_id: 'dataset_storage_id',
                scores: [{ score: 1, task_id: 'task_id_score' }],
            };

            expect(
                getJobEntity({
                    ...generalJobDTO,
                    type: JobType.TRAIN,
                    metadata: { project, task, trained_model: trainedModel },
                })
            ).toEqual(
                expect.objectContaining({
                    type: JobType.TRAIN,
                    metadata: {
                        project,
                        task: {
                            taskId: task.task_id,
                            modelTemplateId: task.model_template_id,
                            datasetStorageId: task.dataset_storage_id,
                            modelArchitecture: task.model_architecture,
                            scores: [{ score: 1, taskId: 'task_id_score' }],
                        },
                        trainedModel: {
                            modelId: 'model-id',
                        },
                    },
                })
            );
        });
    });
});
