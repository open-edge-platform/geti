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
export const detectionLabels = [
    {
        color: '#cc94daff',
        group: 'Detection',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f1',
        is_anomalous: false,
        is_empty: false,
        name: 'Fish',
        parent_id: null,
    },
    {
        color: '#e4a8b2ff',
        group: 'No object',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f3',
        is_anomalous: false,
        is_empty: true,
        name: 'No object',
        parent_id: null,
    },
];

export const classificationLabels = [
    {
        color: '#edb200ff',
        group: 'Detection___Species',
        hotkey: '',
        id: 'ClownFish',
        is_anomalous: false,
        is_empty: false,
        name: 'Clownfish',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },
    {
        color: '#c9e649ff',
        group: 'Detection___Species',
        hotkey: '',
        id: 'YellowFish',
        is_anomalous: false,
        is_empty: false,
        name: 'Yellow Fish',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },
    {
        color: '#9b5de5ff',
        group: 'Detection___Species',
        hotkey: '',
        id: 'BlueFish',
        is_anomalous: false,
        is_empty: false,
        name: 'Blue fish',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },
    {
        color: '#00a5cfff',
        group: 'Detection___Species',
        hotkey: '',
        id: 'RedYellowFish',
        is_anomalous: false,
        is_empty: false,
        name: 'Red yellow fish',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },

    {
        color: '#00a5cfff',
        group: 'Detection___Species',
        hotkey: '',
        id: 'GoldFish',
        is_anomalous: false,
        is_empty: false,
        name: 'Goldfish',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },
    {
        color: '#00a5cfff',
        group: 'Detection___Species',
        hotkey: '',
        id: 'SiameseFish',
        is_anomalous: false,
        is_empty: false,
        name: 'Siamese fish',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },
    {
        color: '#00a5cfff',
        group: 'Detection___Species',
        hotkey: '',
        id: 'Tuna',
        is_anomalous: false,
        is_empty: false,
        name: 'Tuna',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },
    {
        color: '#ba10a4ff',
        group: 'No class',
        hotkey: '',
        id: '63283aedc80c9c686fd3b204',
        is_anomalous: false,
        is_empty: true,
        name: 'No class',
        parent_id: '63283aedc80c9c686fd3b1f1',
    },
];

export const project = {
    creation_time: '2022-09-19T09:48:29.261000+00:00',
    creator_id: 'admin@intel.com',
    datasets: [
        {
            creation_time: '2022-09-19T09:48:29.259000+00:00',
            id: '63283aedc80c9c686fd3b1e7',
            name: 'Default dataset',
            use_for_training: true,
        },
    ],
    id: '63283aedc80c9c686fd3b1e6',
    name: 'Card detection classification',
    performance: {
        score: 0.1,
        task_performances: [
            {
                score: {
                    value: 0.0,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
            {
                score: {
                    value: 0.2,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id-2',
            },
        ],
    },
    pipeline: {
        connections: [
            { from: '63283aedc80c9c686fd3b1e2', to: '63283aedc80c9c686fd3b1e3' },
            { from: '63283aedc80c9c686fd3b1e3', to: '63283aedc80c9c686fd3b1e4' },
            { from: '63283aedc80c9c686fd3b1e4', to: '63283aedc80c9c686fd3b1e5' },
        ],
        tasks: [
            { id: '63283aedc80c9c686fd3b1e2', task_type: 'dataset', title: 'Dataset' },
            {
                id: '63283aedc80c9c686fd3b1e3',
                label_schema_id: '63283aedc80c9c686fd3b1f5',
                labels: detectionLabels,
                task_type: 'detection',
                title: 'Detection',
            },
            { id: '63283aedc80c9c686fd3b1e4', task_type: 'crop', title: 'Crop' },
            {
                id: '6101254defba22ca453f11d1',
                label_schema_id: '63283aedc80c9c686fd3b206',
                labels: classificationLabels,
                task_type: 'classification',
                title: 'Classification',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/63230739c80c9c686fd3a7ce/projects/63283aedc80c9c686fd3b1e6/thumbnail',
};
