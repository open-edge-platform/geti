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

export const modelGroups = {
    model_groups: [
        {
            id: '672d00c843da978dfb79fe98',
            name: 'SAM',
            model_template_id: 'visual_prompting_model',
            task_id: '6101254defba22ca453f11d1',
            models: [
                {
                    id: '672d00c843da978dfb79fe9a',
                    name: 'SAM',
                    creation_date: '2024-11-07T18:02:48.377000+00:00',
                    active_model: false,
                    size: 49254642,
                    performance: {
                        score: 0.7807059616222896,
                    },
                    label_schema_in_sync: true,
                    version: 1,
                    purge_info: {
                        is_purged: false,
                        purge_time: null,
                        user_uid: null,
                    },
                },
            ],
            learning_approach: 'one_shot',
            lifecycle_stage: 'active',
        },
    ],
};

export const modelDetail = {
    id: '672d00c843da978dfb79fe9a',
    name: 'SAM',
    architecture: 'SAM',
    version: 1,
    creation_date: '2024-11-07T18:02:48.377000+00:00',
    size: 49254642,
    performance: {
        score: 0.7807059616222896,
    },
    label_schema_in_sync: true,
    precision: ['FP32'],
    optimized_models: [],
    labels: [
        {
            id: '6101254defba22ca453f11c6',
            name: 'Card',
            is_anomalous: false,
            color: '#81407bff',
            hotkey: '',
            is_empty: false,
            group: 'Instance segmentation labels',
            parent_id: null,
        },
        {
            id: '672cfd8046d386c537aafb05',
            name: 'Empty',
            is_anomalous: false,
            color: '#000000ff',
            hotkey: '',
            is_empty: true,
            group: 'Empty',
            parent_id: null,
        },
    ],
    training_dataset_info: {
        dataset_storage_id: '672cfd8046d386c537aafb02',
        dataset_revision_id: '672d00c843da978dfb79fe99',
        n_samples: 1,
        n_images: 1,
        n_videos: 0,
        n_frames: 0,
    },
    training_framework: {
        type: 'geti_vps',
        version: '1.0',
    },
    purge_info: {
        is_purged: false,
        purge_time: null,
        user_uid: null,
    },
    total_disk_size: 48263259,
    learning_approach: 'one_shot',
    previous_revision_id: '',
    previous_trained_revision_id: '',
};

export const testResults = [
    {
        creation_time: '2024-11-07T18:03:11.673000+00:00',
        datasets_info: [
            {
                id: '672cfd8046d386c537aafb02',
                is_deleted: false,
                n_frames: 0,
                n_images: 129,
                n_samples: 129,
                name: 'Dataset',
            },
        ],
        id: '672d00df055da73fae2a4451',
        job_info: {
            id: '672d00df17709684cdea4956',
            status: 'DONE',
        },
        model_info: {
            group_id: '672d00c843da978dfb79fe98',
            id: '672d00c843da978dfb79fe9a',
            n_labels: 1,
            optimization_type: 'NONE',
            precision: ['FP32'],
            task_id: '6101254defba22ca453f11d1',
            task_type: 'VISUAL_PROMPTING',
            template_id: 'visual_prompting_model',
            version: 1,
        },
        name: 'T1',
        scores: [
            { label_id: null, name: 'Dice', value: 0.9513264945217998 },
            { label_id: '672cfd8046d386c537aafb01', name: 'Card', value: 0.9513264945217998 },
        ],
    },
];

export const test = {
    creation_time: '2024-11-07T18:03:11.673000+00:00',
    datasets_info: [
        {
            id: '672cfd8046d386c537aafb02',
            is_deleted: false,
            n_frames: 0,
            n_images: 129,
            n_samples: 129,
            name: 'Dataset',
        },
    ],
    id: '672d00df055da73fae2a4451',
    job_info: {
        id: '672d00df17709684cdea4956',
        status: 'DONE',
    },
    model_info: {
        group_id: '672d00c843da978dfb79fe98',
        id: '672d00c843da978dfb79fe9a',
        n_labels: 1,
        optimization_type: 'NONE',
        precision: ['FP32'],
        task_id: '6101254defba22ca453f11d1',
        task_type: 'VISUAL_PROMPTING',
        template_id: 'visual_prompting_model',
        version: 1,
    },
    name: 'T1',
    scores: [
        {
            label_id: null,
            name: 'Dice',
            value: 0.9513264945217998,
        },
        {
            label_id: '672cfd8046d386c537aafb01',
            name: 'Card',
            value: 0.9513264945217998,
        },
    ],
};
