// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

export const labels = [
    {
        id: '65cb265bab0427f55cf47140',
        name: 'Spades',
        is_anomalous: false,
        color: '#edb200ff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Suit',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47141',
        name: 'Clubs',
        is_anomalous: false,
        color: '#26518eff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Suit',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47142',
        name: 'Diamonds',
        is_anomalous: false,
        color: '#f7dab3ff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Suit',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47143',
        name: 'Hearts',
        is_anomalous: false,
        color: '#f15b85ff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Suit',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47144',
        name: '7',
        is_anomalous: false,
        color: '#708541ff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47145',
        name: '8',
        is_anomalous: false,
        color: '#00a5cfff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47146',
        name: '9',
        is_anomalous: false,
        color: '#00f5d4ff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47147',
        name: '10',
        is_anomalous: false,
        color: '#c9e649ff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47148',
        name: 'J',
        is_anomalous: false,
        color: '#5b69ffff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf47149',
        name: 'Q',
        is_anomalous: false,
        color: '#80e9afff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf4714a',
        name: 'K',
        is_anomalous: false,
        color: '#25a18eff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
    {
        id: '65cb265bab0427f55cf4714b',
        name: 'A',
        is_anomalous: false,
        color: '#80e9afff',
        hotkey: '',
        is_empty: false,
        is_background: false,
        group: 'Value',
        parent_id: null,
    },
];

export const project = {
    id: '65cb265bab0427f55cf4713b',
    name: 'Card classification',
    creation_time: '2024-02-13T08:20:43.606000+00:00',
    creator_id: 'c74a4a38-2d7e-47b0-a5fd-27dd73679eff',
    pipeline: {
        tasks: [
            {
                id: '65cb265bab0427f55cf4713c',
                title: 'Dataset',
                task_type: 'dataset',
            },
            {
                id: '65cb265bab0427f55cf4713e',
                title: 'Classification',
                task_type: 'classification',
                labels,
                label_schema_id: '65cb265bab0427f55cf47150',
            },
        ],
        connections: [
            {
                from: '65cb265bab0427f55cf4713c',
                to: '65cb265bab0427f55cf4713e',
            },
        ],
    },
    datasets: [
        {
            id: '65cb265bab0427f55cf4714c',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2024-02-13T08:20:43.604000+00:00',
        },
    ],
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/7e69764d-1494-4ffa-8a5f-d5fb1e4405cd/workspaces/08c04c57-fbdd-486c-b29e-7649739351f0/projects/65cb265bab0427f55cf4713b/thumbnail',
    performance: {
        score: null,
        task_performances: [
            {
                task_id: '65cb265bab0427f55cf4713e',
                score: null,
            },
        ],
    },
    storage_info: {},
};

const roi = { height: 960, width: 720 };

export const media = {
    id: '613a23866674c43ae7a777aa',
    uploader_id: 'user@company.com',
    media_information: {
        display_url: '/v2/projects/60d3549a3e6080a926e5ef12/media/images/613a23866674c43ae7a777aa/display/full',
        ...roi,
    },
    name: 'Ace of spades',
    // To revisit makes it so that we can save the current annotation :)
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
    thumbnail: '/v2/projects/60d3549a3e6080a926e5ef12/media/images/613a23866674c43ae7a777aa/display/thumb',
    type: 'image',
    upload_time: '2021-06-29T17:13:44.719000+00:00',
};

export const modelSource = {
    user_id: null,
    model_id: '61387685df33ae8280c347b2',
    model_storage_id: '62387685df33ae8280c63a34',
};

export const userSource = {
    user_id: '25c589ef-1ad0-4d9f-85dd-6085aa250f5d',
    model_id: null,
    model_storage_id: null,
};

export const globalAnnotationDTO = {
    id: 'da1ac62b-886a-4a24-b650-1ef3f9513077',
    labels: [],
    labels_to_revisit: ['61387685df33ae8280c33d9d', '61387685df33ae8280c33d9e'],
    modified: '2021-09-08T12:43:22.265000+00:00',
    shape: { type: 'RECTANGLE', ...roi },
};

export const userAnnotationsResponse = {
    annotations: [],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'annotation',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    labels_to_revisit_full_scene: ['61387685df33ae8280c33d9d'],
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
};
