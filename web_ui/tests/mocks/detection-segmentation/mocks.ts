// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

export const animalLabelId = '635fce72fc03e87df9becd1e';
export const deerLabelId = '635fce72fc03e87df9becd23';

export const detectionLabels = [
    {
        color: '#076984ff',
        group: 'Detection labels',
        hotkey: '',
        id: animalLabelId,
        is_anomalous: false,
        is_empty: false,
        name: 'animal',
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

export const segmentationLabels = [
    {
        color: '#d320d7ff',
        group: 'Detection labels___Segmentation labels',
        hotkey: '',
        id: deerLabelId,
        is_anomalous: false,
        is_empty: false,
        name: 'deer',
        parent_id: null,
    },
    {
        color: '#9e9ef5ff',
        group: 'Empty',
        hotkey: '',
        id: '635fce72fc03e87df9becd25',
        is_anomalous: false,
        is_empty: true,
        name: 'Empty',
        parent_id: null,
    },
];

export const project = {
    creation_time: '2022-10-31T13:32:34.842000+00:00',
    creator_id: 'admin@intel.com',
    datasets: [
        {
            creation_time: '2022-10-31T13:32:34.840000+00:00',
            id: '635fce72fc03e87df9becd14',
            name: 'Dataset',
            use_for_training: true,
        },
    ],
    id: '635fce72fc03e87df9becd13',
    name: 'Detection Segmentation',
    pipeline: {
        connections: [
            {
                from: '635fce72fc03e87df9becd0f',
                to: '635fce72fc03e87df9becd10',
            },
            {
                from: '635fce72fc03e87df9becd10',
                to: '635fce72fc03e87df9becd11',
            },
            {
                from: '635fce72fc03e87df9becd11',
                to: '635fce72fc03e87df9becd12',
            },
        ],
        tasks: [
            {
                id: '635fce72fc03e87df9becd0f',
                task_type: 'dataset',
                title: 'Dataset',
            },
            {
                id: '635fce72fc03e87df9becd10',
                label_schema_id: '635fce72fc03e87df9becd22',
                labels: detectionLabels,
                task_type: 'detection',
                title: 'Detection',
            },
            {
                id: '635fce72fc03e87df9becd11',
                task_type: 'crop',
                title: 'Crop',
            },
            {
                id: '635fce72fc03e87df9becd12',
                label_schema_id: '635fce72fc03e87df9becd27',
                labels: segmentationLabels,
                task_type: 'segmentation',
                title: 'Segmentation',
            },
        ],
    },
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
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/635aa7edfc03e87df9becc19/projects/635fce72fc03e87df9becd13/thumbnail',
};

const roi = { x: 0, y: 0, width: 600, height: 400 };
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
    annotation_state_per_task: [],
    thumbnail:
        // eslint-disable-next-line max-len
        '/v2/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/635aa7edfc03e87df9becc19/projects/60d3549a3e6080a926e5ef12/media/images/613a23866674c43ae7a777aa/display/thumb',
    type: 'image',
    upload_time: '2021-06-29T17:13:44.719000+00:00',
};

export const userAnnotationId = '635fd248c9d1aed75d00f89a';
export const userAnnotationsResponse = {
    annotations: [
        {
            id: userAnnotationId,
            labels: [
                {
                    ...detectionLabels[0],
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
            shape: {
                x: 244,
                y: 106,
                width: 508,
                height: 436,
                type: 'RECTANGLE',
            },
        },
        {
            id: '635fd248c9d1aed75d00f90a',
            labels: [
                {
                    ...detectionLabels[0],
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
            shape: {
                x: 114,
                y: 112,
                width: 90,
                height: 108,
                type: 'RECTANGLE',
            },
        },
    ],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'annotation',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    labels_to_revisit_full_scene: ['61387685df33ae8280c33d9d'],
    annotation_state_per_task: [],
};

export const userAnnotationsDetectionSegmentationResponse = {
    ...userAnnotationsResponse,
    annotations: [
        ...userAnnotationsResponse.annotations,
        {
            id: '635fd248c9d1aed75d00fs0s',
            labels: [
                {
                    ...segmentationLabels[0],
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
            shape: {
                x: 160,
                y: 120,
                width: 90,
                height: 90,
                type: 'RECTANGLE',
            },
        },
        {
            id: '635fd248c9d1aed75d00f80s',
            labels: [
                {
                    ...segmentationLabels[0],
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
            shape: {
                x: 250,
                y: 350,
                width: 90,
                height: 90,
                type: 'RECTANGLE',
            },
        },
    ],
};

export const predictionAnnotationId = userAnnotationId;
export const predictionAnnotationsResponse = {
    annotations: [
        {
            id: predictionAnnotationId,
            labels: [
                {
                    ...detectionLabels[0],
                    probability: 0.8,
                    source: {
                        user_id: null,
                        model_id: '635bdb65bbdc318d614a4412',
                        model_storage_id: '635bda92fc03e87df9becc4d',
                    },
                },
            ],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: {
                x: 244,
                y: 106,
                width: 508,
                height: 436,
                type: 'RECTANGLE',
            },
        },
        {
            id: '635fd248c9d1aed75d00f88c',
            labels: [
                {
                    ...segmentationLabels[0],
                    probability: 0.6705748943766212,
                    source: {
                        user_id: null,
                        model_id: '635bdb65bbdc318d614a4412',
                        model_storage_id: '635bda92fc03e87df9becc4d',
                    },
                },
            ],
            modified: '2022-10-31T13:49:11.124000+00:00',
            shape: {
                points: [
                    { x: 746.9457537918411, y: 161.9387094665272 },
                    { x: 740.6035877196017, y: 198.81240790517228 },
                    { x: 712.7436094403766, y: 220.16159453451883 },
                    { x: 712.1299195868202, y: 241.18014513598325 },
                    { x: 701.7411087866109, y: 293.05522685669456 },
                    { x: 679.0690213127615, y: 298.6149156642259 },
                    { x: 663.2421057792887, y: 275.64933642782427 },
                    { x: 651.9909290010461, y: 251.90456655334725 },
                    { x: 648.5738755230126, y: 221.52881472280336 },
                    { x: 610.1660237970711, y: 198.36919782949792 },
                    { x: 599.9996240847281, y: 171.03306419979077 },
                    { x: 649.2743364278243, y: 111.24913376046021 },
                    { x: 712.4046319299164, y: 109.92560146443515 },
                ],
                type: 'POLYGON',
            },
        },
        {
            id: '635fd248c9d1aed75d00f90a',
            labels: [
                {
                    ...detectionLabels[0],
                    probability: 1,
                    source: {
                        user_id: null,
                        model_id: '635bdb65bbdc318d614a4412',
                        model_storage_id: '635bda92fc03e87df9becc4d',
                    },
                },
            ],
            labels_to_revisit: ['61387685df33ae8280c33d9d', '61387685df33ae8280c33d9e'],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: {
                x: 114,
                y: 112,
                width: 90,
                height: 108,
                type: 'RECTANGLE',
            },
        },
        {
            id: '635fd248c9d1aed75d00f89c',
            labels: [
                {
                    ...segmentationLabels[0],
                    probability: 0.6705748943766212,
                    source: {
                        user_id: null,
                        model_id: '635bdb65bbdc318d614a4412',
                        model_storage_id: '635bda92fc03e87df9becc4d',
                    },
                },
            ],
            modified: '2022-10-31T13:49:11.124000+00:00',
            shape: {
                points: [
                    { x: 156.81829159488063, y: 127.72172655673148 },
                    { x: 170.1558592728491, y: 140.81002079792103 },
                    { x: 176.81829159488063, y: 140.72172655673148 },
                    { x: 187.81829159488063, y: 147.72172655673148 },
                    { x: 192.81829159488063, y: 156.72172655673148 },
                    { x: 194.94451989923357, y: 170.9694627127623 },
                    { x: 191.7988878231814, y: 184.16097375755677 },
                    { x: 182.9185384815619, y: 187.25936164827792 },
                    { x: 166.20655687929755, y: 192.56836207899414 },
                    { x: 155.08911748722275, y: 192.3041061412634 },
                    { x: 145.9460697084878, y: 181.42807934456144 },
                    { x: 139.6371538827433, y: 168.32067333299364 },
                    { x: 134.1433300456771, y: 160.851419548844 },
                    { x: 132.12221341387792, y: 150.31596622002294 },
                    { x: 124.32484616676987, y: 135.13968022445314 },
                    { x: 123.32484616676987, y: 119.72172655673148 },
                    { x: 130.15041763489688, y: 128.58104513338745 },
                    { x: 152.61165317513806, y: 128.67449517030596 },
                    { x: 152.81829159488063, y: 119.72172655673148 },
                ],
                type: 'POLYGON',
            },
        },
    ],
    id: '635fd22cbbdc318d614a54d2',
    kind: 'prediction',
    maps: [
        {
            id: '635fd248c9d1aed75d00f8a5',
            label_id: '635bda92fc03e87df9becc55',
            name: 'Soft Prediction',
            roi: {
                id: '635fd21e36e6f2a794c74b08',
                shape: {
                    height: 224.06939697265625,
                    type: 'RECTANGLE',
                    width: 180.5426025390625,
                    x: 1035.6143798828125,
                    y: 166.19476318359375,
                },
            },
            // eslint-disable-next-line max-len
            url: '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/635aa7edfc03e87df9becc19/projects/635bda92fc03e87df9becc45/datasets/635bda92fc03e87df9becc46/media/videos/635bdaa6fc03e87df9becc5a/frames/690/predictions/maps/635fd248c9d1aed75d00f8a5',
        },
    ],
    media_identifier: {
        type: 'image',
        image_id: '635bdab1fc03e87df9beccb4',
    },
    modified: '2022-10-31T13:47:17.402000+00:00',
};
