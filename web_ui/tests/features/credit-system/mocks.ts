// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { JobCostPropsDTO } from '../../../src/core/jobs/dtos/jobs-dto.interface';
import { GETI_SYSTEM_AUTHOR_ID, JobState, JobType } from '../../../src/core/jobs/jobs.const';
import { OpenApiResponseBody } from '../../../src/core/server/types';
import { getMockedJob } from '../project-dataset/utils';
import { yoloAlgorithm } from '../project-models/mocks';

export const projectId = '60db493ed20945a0046f56ce';
export const detectionTaskId = '60db493fd20945a0046f56d2';

export const getScheduledTrainingJob = (job = getMockedJob({ state: JobState.SCHEDULED })) => ({
    jobs: [
        {
            ...job,
            type: JobType.TRAIN,
            metadata: {
                project: {
                    id: '662f70313090f9f2aa13b7ed',
                    name: 'Candy',
                },
                task: {
                    task_id: '662f70313090f9f2aa13b7f0',
                    name: 'Detection',
                    model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
                    model_architecture: 'MobileNetV2-ATSS',
                    dataset_storage_id: '662f70313090f9f2aa13b7f4',
                },
            },
        },
    ],
    jobs_count: {
        n_scheduled_jobs: 1,
        n_running_jobs: 0,
        n_finished_jobs: 0,
        n_failed_jobs: 0,
        n_cancelled_jobs: 0,
    },
});

export const getScheduledAutoTrainingJob = (
    job = getMockedJob({ state: JobState.SCHEDULED, author: GETI_SYSTEM_AUTHOR_ID })
) => ({
    jobs: [
        {
            ...job,
            type: JobType.TRAIN,
            metadata: {
                project: {
                    id: '662f70313090f9f2aa13b7ed',
                    name: 'Candy',
                },
                task: {
                    task_id: '662f70313090f9f2aa13b7f0',
                    name: 'Detection',
                    model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
                    model_architecture: 'MobileNetV2-ATSS',
                    dataset_storage_id: '662f70313090f9f2aa13b7f4',
                },
            },
        },
    ],
    jobs_count: {
        n_scheduled_jobs: 1,
        n_running_jobs: 0,
        n_finished_jobs: 0,
        n_failed_jobs: 0,
        n_cancelled_jobs: 0,
    },
});

export const getFinishedTrainingJob = (job = getMockedJob({ state: JobState.FINISHED })) => ({
    jobs: [
        {
            ...job,
            type: JobType.TRAIN,
            metadata: {
                project: {
                    id: '662f70313090f9f2aa13b7ed',
                    name: 'Candy',
                },
                task: {
                    task_id: '662f70313090f9f2aa13b7f0',
                    name: 'Detection',
                    model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
                    model_architecture: 'MobileNetV2-ATSS',
                    dataset_storage_id: '662f70313090f9f2aa13b7f4',
                },
                trained_model: {
                    model_id: 'model-id',
                },
            },
        },
    ],
    jobs_count: {
        n_scheduled_jobs: 0,
        n_running_jobs: 0,
        n_finished_jobs: 1,
        n_failed_jobs: 0,
        n_cancelled_jobs: 0,
    },
});

export const getFinishedAutoTrainingJob = (
    job = getMockedJob({ state: JobState.FINISHED, author: GETI_SYSTEM_AUTHOR_ID })
) => ({
    jobs: [
        {
            ...job,
            type: JobType.TRAIN,
            metadata: {
                project: {
                    id: '662f70313090f9f2aa13b7ed',
                    name: 'Candy',
                },
                task: {
                    task_id: '662f70313090f9f2aa13b7f0',
                    name: 'Detection',
                    model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
                    model_architecture: 'MobileNetV2-ATSS',
                    dataset_storage_id: '662f70313090f9f2aa13b7f4',
                },
                trained_model: {
                    model_id: '6343d5e4aba8c6d87d17ab6a',
                },
            },
        },
    ],
    jobs_count: {
        n_scheduled_jobs: 0,
        n_running_jobs: 0,
        n_finished_jobs: 1,
        n_failed_jobs: 0,
        n_cancelled_jobs: 0,
    },
});

export const getEmptyJobs = () => ({
    jobs: [],
    jobs_count: {
        n_scheduled_jobs: 0,
        n_running_jobs: 0,
        n_finished_jobs: 0,
        n_failed_jobs: 0,
        n_cancelled_jobs: 0,
    },
});

export const getScheduledAutoTrainingCostJob = (consumed: JobCostPropsDTO['consumed']) =>
    getScheduledAutoTrainingJob(
        getMockedJob({
            state: JobState.SCHEDULED,
            author: GETI_SYSTEM_AUTHOR_ID,
            cost: {
                requests: [{ unit: 'images', amount: 6 }],
                lease_id: '123',
                consumed,
            },
        })
    );

export const getScheduledTrainingCostJob = (consumed: JobCostPropsDTO['consumed']) =>
    getScheduledTrainingJob(
        getMockedJob({
            state: JobState.SCHEDULED,
            cost: {
                requests: [{ unit: 'images', amount: 6 }],
                lease_id: '123',
                consumed,
            },
        })
    );

export const projectConfigAutoTrainingOnMock = {
    global: [],
    task_chain: [
        {
            components: [
                {
                    description: 'General settings for a task.',
                    entity_identifier: {
                        component: 'TASK_NODE',
                        project_id: '65fd5dde32fa8ee3491d6c92',
                        task_id: detectionTaskId,

                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: 'e7298c67-ef65-40f6-a489-c7dc17c26766',
                    },
                    header: 'General',
                    id: '65fd5df7e6767ac9611de29d',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                'Enable to allow the task to start training automatically when it is ready to train.',
                            editable: true,
                            header: 'Auto-training',
                            name: 'auto_training',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
                {
                    description: 'Specify the number of required annotations for a task',
                    entity_identifier: {
                        component: 'DATASET_COUNTER',
                        project_id: '4dbaf08393691189a1c129eb',
                        task_id: '4dbaf08393691189a1c129ee',
                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: '8c958be2-68ea-437a-8a35-43ff1ecf5192',
                    },
                    header: 'Annotation requirements',
                    id: '4dbaf083bee39aa0eac8f805',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: false,
                            description:
                                // eslint-disable-next-line max-len
                                'Only applicable if auto-training is on. Set this parameter on to let the system dynamically compute the number of required annotations between training rounds based on model performance and training dataset size.',
                            editable: true,
                            header: 'Dynamic required annotations',
                            name: 'use_dynamic_required_annotations',
                            template_type: 'input',
                            ui_rules: {},
                            value: false,
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
            ],
            task_id: detectionTaskId,

            task_title: 'Detection',
        },
        {
            components: [
                {
                    description: 'General settings for a task.',
                    entity_identifier: {
                        component: 'TASK_NODE',
                        project_id: '65fd5dde32fa8ee3491d6c92',
                        task_id: '60db493fd20945a0046f56d6',
                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: 'e7298c67-ef65-40f6-a489-c7dc17c26766',
                    },
                    header: 'General',
                    id: '65fd5df7e6767ac9611de2a4',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                'Enable to allow the task to start training automatically when it is ready to train.',
                            editable: true,
                            header: 'Auto-training',
                            name: 'auto_training',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
                {
                    description: 'Specify the number of required annotations for a task',
                    entity_identifier: {
                        component: 'DATASET_COUNTER',
                        project_id: '4dbaf08393691189a1c129eb',
                        task_id: '4dbaf08393691189a1c129ee',
                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: '8c958be2-68ea-437a-8a35-43ff1ecf5192',
                    },
                    header: 'Annotation requirements',
                    id: '4dbaf083bee39aa0eac8f805',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: false,
                            description:
                                // eslint-disable-next-line max-len
                                'Only applicable if auto-training is on. Set this parameter on to let the system dynamically compute the number of required annotations between training rounds based on model performance and training dataset size.',
                            editable: true,
                            header: 'Dynamic required annotations',
                            name: 'use_dynamic_required_annotations',
                            template_type: 'input',
                            ui_rules: {},
                            value: false,
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
            ],
            task_id: '60db493fd20945a0046f56d6',
            task_title: 'Classification',
        },
    ],
};

export const projectConfigAutoTrainingOffMock = {
    ...projectConfigAutoTrainingOnMock,
    task_chain: projectConfigAutoTrainingOnMock.task_chain.map((taskChain) => ({
        ...taskChain,
        components: taskChain.components.map((component) => ({
            ...component,
            parameters: component.parameters.map((parameters) => ({ ...parameters, value: false })),
        })),
    })),
};

export const modelGroups = {
    model_groups: [
        {
            id: '60dc3b8b3fc7834f46ea90d5',
            name: yoloAlgorithm.name,
            task_id: detectionTaskId,

            model_template_id: yoloAlgorithm.model_template_id,
            models: [
                {
                    name: 'Model of Yolo',
                    creation_date: '2021-06-30T09:38:19.677000+00:00',
                    id: '60dc3b8b3fc7834f46ea90ag',
                    size: 12813101,
                    version: 1,
                    performance: {
                        score: 0.28953322601318,
                    },
                    label_schema_in_sync: false,
                    score_up_to_date: true,
                    active_model: false,
                },
                {
                    name: 'Model of Yolo',
                    creation_date: '2021-06-30T09:38:19.677000+00:00',
                    id: '60dc3b8b3fc7834f46ea90af',
                    size: 12813101,
                    version: 2,
                    performance: {
                        score: 0.28953322601318,
                    },
                    label_schema_in_sync: true,
                    score_up_to_date: true,
                    active_model: true,
                },
            ],
        },
    ],
};

export const modelGroup: OpenApiResponseBody<'GetModelGroup'> = {
    id: '633aa0e210ccb847ccccc42b',
    model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
    models: [
        {
            active_model: true,
            creation_date: '2022-10-10T08:20:52.540000+00:00',
            id: '6343d5e4aba8c6d87d17ab6a',
            name: 'EfficientNet-B0',
            performance: { score: 0.85 },
            size: 16330443,
            version: 2,
        },
        {
            active_model: false,
            creation_date: '2022-10-03T08:44:35.074000+00:00',
            id: '633aa0f397e2d10e57eccdb7',
            name: 'EfficientNet-B0',
            performance: { score: 0.75 },
            size: 16330444,
            version: 1,
        },
    ],
    name: 'EfficientNet-B0',
    task_id: '6101254defba22ca453f11d1',
};

export const supportedAlgorithms: OpenApiResponseBody<'GetSupportedAlgorithms'> = {
    supported_algorithms: [
        {
            name: 'U-Net',
            gigaflops: 5.6,
            model_size: 21.1,
            model_template_id: 'U-Net',
            summary: 'This algorithm is only used for testing purposes',
            task_type: 'detection',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
    ],
};
