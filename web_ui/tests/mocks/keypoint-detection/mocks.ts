// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.
const roi = { x: 0, y: 0, width: 600, height: 400 };

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

export const labels = {
    head: { id: '67abce5e9a4f0d5e2ef030aa', name: 'head', score: 0.17096909880638123 },
    back: { id: '67abce5e9a4f0d5e2ef030ab', name: 'back', score: 0.09705155342817307 },
    back2: { id: '67abce5e9a4f0d5e2ef030ac', name: 'back_2', score: 0.12235713005065918 },
    rightBackLeg: { id: '67abce5e9a4f0d5e2ef030ad', name: 'right_back_leg', score: 0.16456741094589233 },
    leftBackLeg: { id: '67abce5e9a4f0d5e2ef030ae', name: 'left_back_leg', score: 0.135525181889534 },
    leftFrontLeg: { id: '67abce5e9a4f0d5e2ef030af', name: 'left_front_leg', score: 0.10736636072397232 },
    rightFrontLeg: { id: '67abce5e9a4f0d5e2ef030b0', name: 'right_front_leg', score: 0.13312141597270966 },
};

export const keypointStructure = {
    edges: [
        {
            nodes: ['67abce5e9a4f0d5e2ef030aa', '67abce5e9a4f0d5e2ef030ab'],
        },
        {
            nodes: ['67abce5e9a4f0d5e2ef030ab', '67abce5e9a4f0d5e2ef030ac'],
        },
        {
            nodes: ['67abce5e9a4f0d5e2ef030ac', '67abce5e9a4f0d5e2ef030ad'],
        },
        {
            nodes: ['67abce5e9a4f0d5e2ef030ac', '67abce5e9a4f0d5e2ef030ae'],
        },
        {
            nodes: ['67abce5e9a4f0d5e2ef030ab', '67abce5e9a4f0d5e2ef030af'],
        },
        {
            nodes: ['67abce5e9a4f0d5e2ef030ab', '67abce5e9a4f0d5e2ef030b0'],
        },
    ],
    positions: [
        {
            label: '67abce5e9a4f0d5e2ef030aa',
            x: 0.7191157347204161,
            y: 0.2866779089376054,
        },
        {
            label: '67abce5e9a4f0d5e2ef030ab',
            x: 0.5825747724317295,
            y: 0.418212478920742,
        },
        {
            label: '67abce5e9a4f0d5e2ef030ac',
            x: 0.27828348504551365,
            y: 0.45193929173693087,
        },
        {
            label: '67abce5e9a4f0d5e2ef030ad',
            x: 0.2964889466840052,
            y: 0.6593591905564924,
        },
        {
            label: '67abce5e9a4f0d5e2ef030ae',
            x: 0.2483745123537061,
            y: 0.654300168634064,
        },
        {
            label: '67abce5e9a4f0d5e2ef030af',
            x: 0.5838751625487646,
            y: 0.6593591905564924,
        },
        {
            label: '67abce5e9a4f0d5e2ef030b0',
            x: 0.6189856957087126,
            y: 0.6492411467116358,
        },
    ],
};

export const project = {
    id: '61012cdb1d38a5e71ef3baf9',
    name: 'Project',
    creation_time: '2025-02-11T22:25:34.131000+00:00',
    creator_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
    pipeline: {
        tasks: [
            {
                id: '6101254defba22ca453f11cc',
                title: 'Dataset',
                task_type: 'dataset',
                keypoint_structure: keypointStructure,
            },
            {
                id: '67abce5e9a4f0d5e2ef030a8',
                title: 'Keypoint detection',
                task_type: 'keypoint_detection',
                labels: [
                    {
                        ...labels.head,
                        is_anomalous: false,
                        color: '#25a18eff',
                        hotkey: '',
                        is_empty: false,
                        group: 'keypoint-detection',
                        parent_id: null,
                    },
                    {
                        ...labels.back,
                        is_anomalous: false,
                        color: '#edb200ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'keypoint-detection',
                        parent_id: null,
                    },
                    {
                        ...labels.back2,
                        is_anomalous: false,
                        color: '#9d3b1aff',
                        hotkey: '',
                        is_empty: false,
                        group: 'keypoint-detection',
                        parent_id: null,
                    },
                    {
                        ...labels.rightBackLeg,
                        is_anomalous: false,
                        color: '#9d3b1aff',
                        hotkey: '',
                        is_empty: false,
                        group: 'keypoint-detection',
                        parent_id: null,
                    },
                    {
                        ...labels.leftBackLeg,
                        is_anomalous: false,
                        color: '#ff5662ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'keypoint-detection',
                        parent_id: null,
                    },
                    {
                        ...labels.leftFrontLeg,
                        is_anomalous: false,
                        color: '#f7dab3ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'keypoint-detection',
                        parent_id: null,
                    },
                    {
                        ...labels.rightFrontLeg,
                        is_anomalous: false,
                        color: '#076984ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'keypoint-detection',
                        parent_id: null,
                    },
                ],
                label_schema_id: '67abce5e9a4f0d5e2ef030b4',
                keypoint_structure: {
                    edges: [
                        {
                            nodes: ['67abce5e9a4f0d5e2ef030aa', '67abce5e9a4f0d5e2ef030ab'],
                        },
                        {
                            nodes: ['67abce5e9a4f0d5e2ef030ab', '67abce5e9a4f0d5e2ef030ac'],
                        },
                        {
                            nodes: ['67abce5e9a4f0d5e2ef030ac', '67abce5e9a4f0d5e2ef030ad'],
                        },
                        {
                            nodes: ['67abce5e9a4f0d5e2ef030ac', '67abce5e9a4f0d5e2ef030ae'],
                        },
                        {
                            nodes: ['67abce5e9a4f0d5e2ef030ab', '67abce5e9a4f0d5e2ef030af'],
                        },
                        {
                            nodes: ['67abce5e9a4f0d5e2ef030ab', '67abce5e9a4f0d5e2ef030b0'],
                        },
                    ],
                    positions: [
                        {
                            label: '67abce5e9a4f0d5e2ef030aa',
                            x: 0.7191157347204161,
                            y: 0.2866779089376054,
                        },
                        {
                            label: '67abce5e9a4f0d5e2ef030ab',
                            x: 0.5825747724317295,
                            y: 0.418212478920742,
                        },
                        {
                            label: '67abce5e9a4f0d5e2ef030ac',
                            x: 0.27828348504551365,
                            y: 0.45193929173693087,
                        },
                        {
                            label: '67abce5e9a4f0d5e2ef030ad',
                            x: 0.2964889466840052,
                            y: 0.6593591905564924,
                        },
                        {
                            label: '67abce5e9a4f0d5e2ef030ae',
                            x: 0.2483745123537061,
                            y: 0.654300168634064,
                        },
                        {
                            label: '67abce5e9a4f0d5e2ef030af',
                            x: 0.5838751625487646,
                            y: 0.6593591905564924,
                        },
                        {
                            label: '67abce5e9a4f0d5e2ef030b0',
                            x: 0.6189856957087126,
                            y: 0.6492411467116358,
                        },
                    ],
                },
            },
        ],
        connections: [
            {
                from: '6101254defba22ca453f11cc',
                to: '67abce5e9a4f0d5e2ef030a8',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/6101254defba22ca453f11c2/projects/6101254defba22ca453f11cd/thumbnail',
    performance: {
        score: null,
        task_performances: [
            {
                task_id: '67abce5e9a4f0d5e2ef030a8',
                score: null,
            },
        ],
    },
    storage_info: {},
    datasets: [
        {
            id: '67abce5e9a4f0d5e2ef030b1',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2025-02-11T22:25:34.129000+00:00',
        },
    ],
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

export const predictionAnnotationsResponse = {
    predictions: [
        {
            labels: [{ ...labels.head, probability: labels.head.score }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: 713,
                y: 223,
            },
        },
        {
            labels: [{ ...labels.back, probability: labels.back.score }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: 564,
                y: 298,
            },
        },
        {
            labels: [{ ...labels.back2, probability: labels.back2.score }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: 353,
                y: 286,
            },
        },
        {
            labels: [{ ...labels.rightBackLeg, probability: labels.rightBackLeg.score }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: 336,
                y: 506,
            },
        },
        {
            labels: [{ ...labels.leftBackLeg, probability: labels.leftBackLeg.score }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: 297,
                y: 483,
            },
        },
        {
            labels: [{ ...labels.leftFrontLeg, probability: labels.leftFrontLeg.score }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: 598,
                y: 547,
            },
        },
        {
            labels: [{ ...labels.rightFrontLeg, probability: labels.rightFrontLeg.score }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: 630,
                y: 524,
            },
        },
    ],
    created: '2025-02-11 22:40:56.159214722 +0000',
    media_identifier: {
        image_id: '67a515e8c965f5e5eb2bf732',
        type: 'image',
    },
};

export const userAnnotationId = '6b3b8453-92a2-41ef-9725-63badb218504';
export const userAnnotationsResponse = {
    kind: 'annotation',
    modified: '2025-02-11T22:39:36.237000+00:00',
    media_identifier: {
        type: 'image',
        image_id: '67abce7a991fc28c29111af6',
    },
    id: '67abd1a852488e0d0ee6ea78',
    labels_to_revisit_full_scene: [],
    annotation_state_per_task: [
        {
            task_id: '67abce5e9a4f0d5e2ef030a8',
            state: 'annotated',
        },
    ],
    annotations: [
        {
            id: '045edd0f-ce03-4ea8-91b0-9a0138b4d1eb',
            modified: '2025-02-11T22:39:36.237000+00:00',
            labels: [
                {
                    id: '67abce5e9a4f0d5e2ef030aa',
                    probability: 1,
                    source: {
                        user_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            shape: {
                type: 'KEYPOINT',
                x: 713,
                y: 223,
                is_visible: true,
            },
        },
        {
            id: 'c11a0a97-5f57-47ce-af8b-cff15be8b984',
            modified: '2025-02-11T22:39:36.237000+00:00',
            labels: [
                {
                    id: '67abce5e9a4f0d5e2ef030ab',
                    probability: 1,
                    source: {
                        user_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            shape: {
                type: 'KEYPOINT',
                x: 564,
                y: 298,
                is_visible: true,
            },
        },
        {
            id: 'bb9e8769-29d9-443c-96d4-fe5bc4413dc2',
            modified: '2025-02-11T22:39:36.237000+00:00',
            labels: [
                {
                    id: '67abce5e9a4f0d5e2ef030ac',
                    probability: 1,
                    source: {
                        user_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            shape: {
                type: 'KEYPOINT',
                x: 353,
                y: 286,
                is_visible: true,
            },
        },
        {
            id: 'ce249698-a905-4d73-9a3a-8e26abd269ff',
            modified: '2025-02-11T22:39:36.237000+00:00',
            labels: [
                {
                    id: '67abce5e9a4f0d5e2ef030ad',
                    probability: 1,
                    source: {
                        user_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            shape: {
                type: 'KEYPOINT',
                x: 336,
                y: 506,
                is_visible: true,
            },
        },
        {
            id: 'ddcbee24-62bf-4906-8497-1fcf0093e5c5',
            modified: '2025-02-11T22:39:36.237000+00:00',
            labels: [
                {
                    id: '67abce5e9a4f0d5e2ef030ae',
                    probability: 1,
                    source: {
                        user_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            shape: {
                type: 'KEYPOINT',
                x: 297,
                y: 483,
                is_visible: true,
            },
        },
        {
            id: 'ce0be561-08d9-4f5d-a63a-dcc5ebee41d8',
            modified: '2025-02-11T22:39:36.237000+00:00',
            labels: [
                {
                    id: '67abce5e9a4f0d5e2ef030af',
                    probability: 1,
                    source: {
                        user_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            shape: {
                type: 'KEYPOINT',
                x: 598,
                y: 547,
                is_visible: true,
            },
        },
        {
            id: '4fb80ca4-9f8d-4d5b-a8f6-3258f1bf03bb',
            modified: '2025-02-11T22:39:36.237000+00:00',
            labels: [
                {
                    id: '67abce5e9a4f0d5e2ef030b0',
                    probability: 1,
                    source: {
                        user_id: 'bea1e909-1a44-4848-bdd1-fc7be2bb76c5',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            shape: {
                type: 'KEYPOINT',
                x: 630,
                y: 524,
                is_visible: true,
            },
        },
    ],
};
