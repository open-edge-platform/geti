// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TASK_TYPE } from '../../../src/core/projects/dtos/task.interface';

const roi = { x: 0, y: 0, width: 600, height: 400 };

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

export const project = {
    creation_time: '2021-07-28T09:37:17.319000+00:00',
    datasets: [
        {
            id: '6101254defba22ca453f11cc',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2022-09-14T12:35:53.070000+00:00',
        },
    ],
    id: '61012cdb1d38a5e71ef3baf9',
    name: 'Example classification project',
    pipeline: {
        connections: [{ from: '6101254defba22ca453f11ce', to: '6101254defba22ca453f11d1' }],
        tasks: [
            { id: '6101254defba22ca453f11ce', task_type: TASK_TYPE.DATASET, title: 'Dataset' },
            {
                id: '6101254defba22ca453f11d1',
                labels: [
                    {
                        color: '#0015ffff',
                        group: 'species',
                        hotkey: 'ctrl+5',
                        id: '6101254defba22ca453f11c6',
                        is_empty: false,
                        is_anomalous: false,
                        parent_id: null,
                        name: 'horse',
                    },
                    {
                        color: '#00ffffff',
                        group: 'species',
                        hotkey: 'ctrl+6',
                        id: '6101254defba22ca453f11c7',
                        is_empty: false,
                        is_anomalous: false,
                        parent_id: null,
                        name: 'donkey',
                    },
                    {
                        color: '#00aaaaff',
                        group: 'saddle_state',
                        hotkey: 'ctrl+7',
                        id: '6101254defba22ca453f11c8',
                        is_empty: false,
                        is_anomalous: false,
                        parent_id: null,
                        name: 'saddled',
                    },
                    {
                        color: '#00aaffff',
                        group: 'saddle_state',
                        hotkey: 'ctrl+8',
                        id: '6101254defba22ca453f11c9',
                        is_empty: false,
                        is_anomalous: false,
                        parent_id: null,
                        name: 'unsaddled',
                    },
                    {
                        color: '#7ada55ff',
                        group: 'No class',
                        hotkey: 'ctrl+0',
                        id: '6101254defba22ca453f11ca',
                        is_empty: true,
                        is_anomalous: false,
                        parent_id: null,
                        name: 'No class',
                    },
                ],
                task_type: TASK_TYPE.CLASSIFICATION,
                title: 'Sample classification',
            },
        ],
    },
    performance: {
        score: 0.7,
        task_performances: [
            {
                score: {
                    value: 0.7,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/6101254defba22ca453f11c2/projects/6101254defba22ca453f11cd/thumbnail',
};

export const media = {
    id: '613a23866674c43ae7a777aa',
    uploader_id: 'user@company.com',
    media_information: {
        display_url: '/v2/projects/60d3549a3e6080a926e5ef12/media/images/613a23866674c43ae7a777aa/display/full',
        height: roi.height,
        width: roi.width,
    },
    name: 'Course completion',
    // To revisit makes it so that we can save the current annotation :)
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
    thumbnail: '/v2/projects/60d3549a3e6080a926e5ef12/media/images/613a23866674c43ae7a777aa/display/thumb',
    type: 'image',
    upload_time: '2021-06-29T17:13:44.719000+00:00',
};

export const userAnnotationId = '6b3b8453-92a2-41ef-9725-63badb218504';
const horseLabelId = '6101254defba22ca453f11c6';
const saddleLabelId = '6101254defba22ca453f11c8';

export const userAnnotationsResponse = {
    annotations: [
        {
            id: userAnnotationId,
            labels: [
                {
                    id: horseLabelId,
                    probability: 1,
                    source: {
                        user_id: 'default_user',
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
                {
                    id: saddleLabelId,
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
            shape: { type: 'RECTANGLE', ...roi },
        },
    ],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'annotation',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    labels_to_revisit_full_scene: ['61387685df33ae8280c33d9d'],
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
};

export const predictionAnnotationId = userAnnotationId;
export const predictionAnnotationsResponse = {
    annotations: [
        {
            id: predictionAnnotationId,
            labels: [
                {
                    id: horseLabelId,
                    probability: 0.87,
                    source: {
                        user_id: null,
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
                {
                    id: saddleLabelId,
                    probability: 0.87,
                    source: {
                        user_id: null,
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
            ],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', ...roi },
        },
    ],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'prediction',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    maps: [
        {
            id: '6450b2eb6d89c127db4cc6dc',
            label_id: horseLabelId,
            name: 'horse',
            roi: {
                id: '6450b2d1986208297a5cbae7',
                shape: {
                    height: 720,
                    type: 'RECTANGLE',
                    width: 1280,
                    x: 0,
                    y: 0,
                },
            },
            // eslint-disable-next-line max-len
            url: '/api/v1/organizations/000000000000000000000001/workspaces/workspace_id/projects/project_id/datasets/dataset_id/media/images/image_id/predictions/maps/map_id',
        },
        {
            id: '6450b2eb6d89c127db4cc6de',
            label_id: saddleLabelId,
            name: 'deer',
            roi: {
                id: '6450b2d1986208297a5cbae7',
                shape: {
                    height: 720,
                    type: 'RECTANGLE',
                    width: 1280,
                    x: 0,
                    y: 0,
                },
            },
            // eslint-disable-next-line max-len
            url: '/api/v1/organizations/000000000000000000000001/workspaces/workspace_id/projects/project_id/datasets/dataset_id/media/images/image_id/predictions/maps/map_id',
        },
    ],
};

export const singeLabelProject = {
    id: '66fead94117b329405566c05',
    name: 'Project',
    creation_time: '2024-10-03T14:43:32.903000+00:00',
    creator_id: 'b8fdde88-f903-4a54-86fa-da61cc513aec',
    pipeline: {
        tasks: [
            {
                id: '66fead94117b329405566c06',
                title: 'Dataset',
                task_type: 'dataset',
            },
            {
                id: '66fead94117b329405566c09',
                title: 'Classification',
                task_type: 'classification',
                labels: [
                    {
                        id: '66fead94117b329405566c0b',
                        name: 'value',
                        is_anomalous: false,
                        color: '#c9e649ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Classification labels',
                        parent_id: null,
                    },
                    {
                        id: '66fead94117b329405566c0c',
                        name: 'suit',
                        is_anomalous: false,
                        color: '#00f5d4ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Classification labels',
                        parent_id: null,
                    },
                ],
                label_schema_id: '66fead94117b329405566c10',
            },
        ],
        connections: [
            {
                from: '66fead94117b329405566c06',
                to: '66fead94117b329405566c09',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/ce9c2143-2df2-42f2-bec9-645564ca0455/workspaces/821a9293-9572-41f4-bb3f-b5ce16763a48/projects/66fead94117b329405566c05/thumbnail',
    performance: {
        score: null,
        task_performances: [
            {
                task_id: '66fead94117b329405566c09',
                score: null,
            },
        ],
    },
    storage_info: {},
    datasets: [
        {
            id: '66fead94117b329405566c0d',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2024-10-03T14:43:32.901000+00:00',
        },
    ],
};
export const hierarchicalLabelsProject = {
    id: '5bc9bb1a25b681e3ca3ff992',
    name: 'Cards hierarchical',
    creation_time: '2024-10-02T12:39:58.959000+00:00',
    creator_id: 'b8fdde88-f903-4a54-86fa-da61cc513aec',
    pipeline: {
        tasks: [
            {
                id: '5bc9bb1a25b681e3ca3ff993',
                title: 'Dataset',
                task_type: 'dataset',
            },
            {
                id: '5bc9bb1a25b681e3ca3ff995',
                title: 'Classification',
                task_type: 'classification',
                labels: [
                    {
                        id: '5bc9bb1a25b681e3ca3ff997',
                        name: 'Red',
                        is_anomalous: false,
                        color: '#e96115ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Color',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff998',
                        name: 'Hearts',
                        is_anomalous: false,
                        color: '#d7bc5eff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Color___Red suit',
                        parent_id: '5bc9bb1a25b681e3ca3ff997',
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff999',
                        name: 'Diamonds',
                        is_anomalous: false,
                        color: '#ff5662ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Color___Red suit',
                        parent_id: '5bc9bb1a25b681e3ca3ff997',
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff99a',
                        name: 'Black',
                        is_anomalous: false,
                        color: '#26518eff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Color',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff99b',
                        name: 'Spades',
                        is_anomalous: false,
                        color: '#c9e649ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Color___Black suit',
                        parent_id: '5bc9bb1a25b681e3ca3ff99a',
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff99c',
                        name: 'Clubs',
                        is_anomalous: false,
                        color: '#25a18eff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Color___Black suit',
                        parent_id: '5bc9bb1a25b681e3ca3ff99a',
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff99d',
                        name: '7',
                        is_anomalous: false,
                        color: '#ff7d00ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff99e',
                        name: '8',
                        is_anomalous: false,
                        color: '#00a5cfff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff99f',
                        name: '9',
                        is_anomalous: false,
                        color: '#f15b85ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff9a0',
                        name: '10',
                        is_anomalous: false,
                        color: '#ff5662ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff9a1',
                        name: 'J',
                        is_anomalous: false,
                        color: '#076984ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff9a2',
                        name: 'Q',
                        is_anomalous: false,
                        color: '#edb200ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff9a3',
                        name: 'K',
                        is_anomalous: false,
                        color: '#00f5d4ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                    {
                        id: '5bc9bb1a25b681e3ca3ff9a4',
                        name: 'A',
                        is_anomalous: false,
                        color: '#708541ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Values',
                        parent_id: null,
                    },
                ],
                label_schema_id: '5bc9bb1a25b681e3ca3ff9ab',
            },
        ],
        connections: [
            {
                from: '5bc9bb1a25b681e3ca3ff993',
                to: '5bc9bb1a25b681e3ca3ff995',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/ce9c2143-2df2-42f2-bec9-645564ca0455/workspaces/821a9293-9572-41f4-bb3f-b5ce16763a48/projects/5bc9bb1a25b681e3ca3ff992/thumbnail',
    performance: {
        score: null,
        task_performances: [
            {
                task_id: '5bc9bb1a25b681e3ca3ff995',
                score: null,
            },
        ],
    },
    storage_info: {},
    datasets: [
        {
            id: '5bc9bb1a25b681e3ca3ff9a5',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2024-10-02T12:39:58.959000+00:00',
        },
    ],
};
export const multiLabelProject = {
    id: '66fd3fe3b8fd1de608886026',
    name: 'multi label',
    creation_time: '2024-10-02T12:43:15.827000+00:00',
    creator_id: 'b8fdde88-f903-4a54-86fa-da61cc513aec',
    pipeline: {
        tasks: [
            {
                id: '66fd3fe3b8fd1de608886027',
                title: 'Dataset',
                task_type: 'dataset',
            },
            {
                id: '66fd3fe3b8fd1de608886029',
                title: 'Classification',
                task_type: 'classification',
                labels: [
                    {
                        id: '66fd3fe3b8fd1de60888602b',
                        name: 'suit',
                        is_anomalous: false,
                        color: '#5b69ffff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Classification labels___suit',
                        parent_id: null,
                    },
                    {
                        id: '66fd3fe3b8fd1de60888602c',
                        name: 'value',
                        is_anomalous: false,
                        color: '#548fadff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Classification labels___value',
                        parent_id: null,
                    },
                    {
                        id: '66fd3fe3b8fd1de608886031',
                        name: 'No class',
                        is_anomalous: false,
                        color: '#000000ff',
                        hotkey: '',
                        is_empty: true,
                        group: 'No class',
                        parent_id: null,
                    },
                ],
                label_schema_id: '66fd3fe3b8fd1de608886033',
            },
        ],
        connections: [
            {
                from: '66fd3fe3b8fd1de608886027',
                to: '66fd3fe3b8fd1de608886029',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/ce9c2143-2df2-42f2-bec9-645564ca0455/workspaces/821a9293-9572-41f4-bb3f-b5ce16763a48/projects/66fd3fe3b8fd1de608886026/thumbnail',
    performance: {
        score: null,
        task_performances: [
            {
                task_id: '66fd3fe3b8fd1de608886029',
                score: null,
            },
        ],
    },
    storage_info: {},
    datasets: [
        {
            id: '66fd3fe3b8fd1de60888602d',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2024-10-02T12:43:15.817000+00:00',
        },
    ],
};
