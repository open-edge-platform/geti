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

export const mockedJobsResponse = {
    jobs: [
        {
            id: '65015a5dadd2d0ffd46da494',
            type: 'train',
            creation_time: '2023-09-13T06:44:45.505000+00:00',
            start_time: '2023-09-13T06:44:53.360000+00:00',
            end_time: '2023-09-13T06:55:41.070000+00:00',
            name: 'Training',
            author: 'admin@intel.com',
            state: 'finished',
            steps: [
                {
                    message: 'Train data retrieved',
                    index: 1,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Retrieve train data',
                },
                {
                    message: 'Train dataset is created',
                    index: 2,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Create train dataset',
                },
                {
                    message: 'Training from sharded dataset is disabled',
                    index: 3,
                    progress: -1,
                    state: 'skipped',
                    step_name: 'Shard dataset',
                },
                {
                    message: 'No previous model found for the project.',
                    index: 4,
                    progress: -1,
                    state: 'skipped',
                    step_name: 'Pre-evaluate model if exists',
                },
                {
                    message: 'Model is trained',
                    index: 5,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Model training',
                },
                {
                    message: 'Model improvement is checked',
                    index: 6,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Trained model evaluation',
                },
                {
                    message: 'Trained model is activated, inference server is initialized',
                    index: 7,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Activate trained model',
                },
                {
                    message: 'The unannotated dataset is empty, skipping the inference',
                    index: 8,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Infer on unannotated dataset for task',
                },
                {
                    message: 'Only one trainable task for project, skipping the pipeline inference',
                    index: 9,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Inference on unannotated dataset with all models chained',
                },
            ],
            cancellation_info: {
                is_cancelled: false,
                user_uid: null,
                cancel_time: null,
            },
            metadata: {
                project: {
                    id: '650159c74c839353a8bac97b',
                    name: 'Tiff images',
                },
                task: {
                    task_id: '650159c74c839353a8bac97e',
                    name: 'Instance segmentation',
                    model_template_id: 'Custom_Counting_Instance_Segmentation_MaskRCNN_ResNet50',
                    model_architecture: 'MaskRCNN-ResNet50',
                    dataset_storage_id: '650159c74c839353a8bac982',
                },
                trained_model: {
                    model_storage_id: '650159c74c839353a8bac97f',
                    model_id: '65015abd637070964b2771b9',
                },
            },
            description: '',
            status: {
                message: '',
                progress: -1,
                time_remaining: -1,
                state: 'finished',
            },
        },
        {
            id: '6502eefcadd2d0ffd46da495',
            type: 'test',
            creation_time: '2023-09-14T11:31:08.066000+00:00',
            start_time: '2023-09-14T11:31:15.337000+00:00',
            end_time: '2023-09-14T11:33:26.761000+00:00',
            name: 'Model testing',
            author: 'admin@intel.com',
            state: 'finished',
            steps: [
                {
                    message: 'Testing dataset created',
                    index: 1,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Creating testing dataset',
                },
                {
                    message: 'Inferring on testing dataset completed',
                    index: 2,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Inferring on testing dataset',
                },
                {
                    message: 'Results evaluated failed',
                    index: 3,
                    progress: -1,
                    state: 'failed',
                    step_name: 'Evaluating results',
                },
            ],
            cancellation_info: {
                is_cancelled: false,
                user_uid: null,
                cancel_time: null,
            },
            metadata: {
                project: {
                    id: '64faf6331e65f3a4ac393624',
                    name: 'Project',
                },
                task: {
                    task_id: '64faf6351e65f3a4ac393628',
                },
                test: {
                    model_template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR',
                    model_architecture: 'Lite-HRNet-18-mod2',
                    datasets: [
                        {
                            id: '64faf6361e65f3a4ac39362c',
                            name: 'Dataset',
                        },
                    ],
                    model: {
                        architecture: 'Lite-HRNet-18-mod2',
                        template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR',
                        id: '64faf745907e6c048a661f68',
                        optimization_type: 'MO',
                        precision: ['FP16'],
                        has_xai_head: false,
                    },
                },
            },
            description: '',
            status: {
                message: '',
                progress: -1,
                time_remaining: -1,
                state: 'finished',
            },
        },
        {
            id: '65100ac2add2d0ffd46da49f',
            type: 'optimize_pot',
            creation_time: '2023-09-24T10:09:06.112000+00:00',
            start_time: '2023-09-24T10:09:13.674000+00:00',
            end_time: null,
            name: 'Optimization',
            author: 'admin@intel.com',
            state: 'running',
            steps: [
                {
                    message: null,
                    index: 1,
                    progress: -1,
                    state: 'skipped',
                    step_name: 'Shard dataset',
                },
                {
                    message: null,
                    index: 2,
                    progress: -1,
                    state: 'waiting',
                    step_name: 'Optimizing model',
                },
                {
                    message: null,
                    index: 3,
                    progress: -1,
                    state: 'waiting',
                    step_name: 'Evaluating optimized model',
                },
            ],
            cancellation_info: {
                is_cancelled: false,
                user_uid: null,
                cancel_time: null,
            },
            metadata: {
                project: {
                    id: '6502f2234c839353a8baca0d',
                    name: 'model_test_result_flowers',
                },
                task: {
                    task_id: '6502f2234c839353a8baca10',
                    model_template_id: 'Custom_Counting_Instance_Segmentation_MaskRCNN_ResNet50',
                    model_architecture: 'MaskRCNN-ResNet50',
                },
                model_storage_id: '6502f2234c839353a8baca11',
                base_model_id: '65100106887fc9004ab911fb',
                optimization_type: 'POT',
                optimized_model_id: null,
            },
            description: '',
            status: {
                message: '',
                progress: -1,
                time_remaining: -1,
                state: 'running',
            },
        },
    ],
    jobs_count: {
        n_scheduled_jobs: 2,
        n_running_jobs: 1,
        n_finished_jobs: 3,
        n_failed_jobs: 4,
        n_cancelled_jobs: 0,
    },
};

export const mockedJobsRunningResponse = {
    jobs: [
        {
            id: '65015a5dadd2d0ffd46da494',
            type: 'train',
            creation_time: '2023-09-13T06:44:45.505000+00:00',
            start_time: '2023-09-13T06:44:53.360000+00:00',
            end_time: '2023-09-13T06:55:41.070000+00:00',
            name: 'Training',
            author: 'admin@intel.com',
            state: 'running',
            steps: [
                {
                    message: null,
                    index: 1,
                    progress: 65,
                    state: 'running',
                    step_name: 'Retrieve train data',
                },
                {
                    message: 'Train dataset is created',
                    index: 2,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Create train dataset',
                },
                {
                    message: 'Training from sharded dataset is disabled',
                    index: 3,
                    progress: -1,
                    state: 'skipped',
                    step_name: 'Shard dataset',
                },
                {
                    message: 'No previous model found for the project.',
                    index: 4,
                    progress: -1,
                    state: 'skipped',
                    step_name: 'Pre-evaluate model if exists',
                },
                {
                    message: 'Model is trained',
                    index: 5,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Model training',
                },
                {
                    message: 'Model improvement is checked',
                    index: 6,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Trained model evaluation',
                },
                {
                    message: 'Trained model is activated, inference server is initialized',
                    index: 7,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Activate trained model',
                },
                {
                    message: 'The unannotated dataset is empty, skipping the inference',
                    index: 8,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Infer on unannotated dataset for task',
                },
                {
                    message: 'Only one trainable task for project, skipping the pipeline inference',
                    index: 9,
                    progress: 100,
                    state: 'finished',
                    step_name: 'Inference on unannotated dataset with all models chained',
                },
            ],
            cancellation_info: {
                is_cancelled: false,
                user_uid: null,
                cancel_time: null,
            },
            metadata: {
                project: {
                    id: '650159c74c839353a8bac97b',
                    name: 'Tiff images',
                },
                task: {
                    task_id: '650159c74c839353a8bac97e',
                    name: 'Instance segmentation task',
                    model_template_id: 'Custom_Counting_Instance_Segmentation_MaskRCNN_ResNet50',
                    model_architecture: 'MaskRCNN-ResNet50',
                    dataset_storage_id: '650159c74c839353a8bac982',
                },
                trained_model: {
                    model_storage_id: '650159c74c839353a8bac97f',
                    model_id: '65015abd637070964b2771b9',
                },
            },
            description: '',
            status: {
                message: '',
                progress: -1,
                time_remaining: -1,
                state: 'finished',
            },
        },
    ],
    jobs_count: {
        n_scheduled_jobs: 2,
        n_running_jobs: 1,
        n_finished_jobs: 3,
        n_failed_jobs: 4,
        n_cancelled_jobs: 0,
    },
};
