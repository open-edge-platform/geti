// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
const roi = { x: 0, y: 0, width: 600, height: 400 };
const roi2 = { x: 50, y: 20, width: 300, height: 50 };

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

export const project = {
    creation_time: '2021-07-28T09:37:17.319000+00:00',
    creator_id: 'Example user',
    datasets: [
        {
            id: '6101254defba22ca453f11cc',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2022-09-14T12:35:53.070000+00:00',
        },
    ],
    id: '61012cdb1d38a5e71ef3baf9',
    name: 'Example Segmentation project',
    pipeline: {
        connections: [{ from: '6101254defba22ca453f11ce', to: '6101254defba22ca453f11d1' }],
        tasks: [
            { id: '6101254defba22ca453f11ce', task_type: 'dataset', title: 'Dataset' },
            {
                id: '6101254defba22ca453f11d1',
                label_schema_id: '6101254defba22ca453f11c2',
                labels: [
                    {
                        color: '#0015ffff',
                        group: 'species',
                        hotkey: 'ctrl+5',
                        id: '6101254defba22ca453f11c6',
                        is_empty: false,
                        is_anomalous: false,
                        name: 'horse',
                    },
                    {
                        color: '#00ffffff',
                        group: 'species',
                        hotkey: 'ctrl+6',
                        id: '6101254defba22ca453f11c7',
                        is_empty: false,
                        is_anomalous: false,
                        name: 'donkey',
                    },
                    {
                        color: '#00aaaaff',
                        group: 'saddle_state',
                        hotkey: 'ctrl+7',
                        id: '6101254defba22ca453f11c8',
                        is_empty: false,
                        is_anomalous: false,
                        name: 'saddled',
                    },
                    {
                        color: '#00aaffff',
                        group: 'saddle_state',
                        hotkey: 'ctrl+8',
                        id: '6101254defba22ca453f11c9',
                        is_empty: false,
                        is_anomalous: false,
                        name: 'unsaddled',
                    },
                    {
                        color: '#7ada55ff',
                        group: 'No class',
                        hotkey: 'ctrl+0',
                        id: '6101254defba22ca453f11ca',
                        is_empty: true,
                        is_anomalous: false,
                        name: 'No class',
                    },
                ],
                task_type: 'segmentation',
                title: 'Sample segmentation',
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

export const predictionAnnotationId = '112233';
const horseLabelId = '6101254defba22ca453f11c6';
const saddleStateLabel = '6101254defba22ca453f11c8';
export const predictionAnnotationsResponse = {
    annotations: [
        {
            id: predictionAnnotationId,
            labels: [
                {
                    id: horseLabelId,
                    probability: 0.1,
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
        {
            id: '221133',
            labels: [
                {
                    id: horseLabelId,
                    probability: 0.4,
                    source: {
                        user_id: null,
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
            ],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', ...roi, x: 200, y: 200 },
        },
        {
            id: '332211',
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
            ],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', ...roi, x: 400, y: 400 },
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
            name: 'Antelope',
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

export const userAnnotationId = '6b3b8453-92a2-41ef-9725-63badb218504';
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

export const userFewAnnotationsResponse = {
    annotations: [
        {
            id: 'user-annotation-id-1',
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
            ],
            labels_to_revisit: ['61387685df33ae8280c33d9d', '61387685df33ae8280c33d9e'],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', ...roi },
        },
        {
            id: 'user-annotation-id-2',
            labels: [
                {
                    id: saddleStateLabel,
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
            shape: { type: 'RECTANGLE', ...roi2 },
        },
    ],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'annotation',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    labels_to_revisit_full_scene: ['61387685df33ae8280c33d9d'],
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
};
