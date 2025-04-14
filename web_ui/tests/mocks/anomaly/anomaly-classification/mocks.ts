// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/632aacee2dc03cc436625975/datasets/632aacee2dc03cc436625976/annotator/image/632c6eae2dc03cc436625a2a';

export const media = {
    annotation_state_per_task: [
        {
            state: 'annotated',
            task_id: '632aacee2dc03cc436625974',
        },
    ],
    id: '632c6eae2dc03cc436625a2a',
    media_information: {
        display_url:
            // eslint-disable-next-line max-len
            '/api/v1/organizations/000000000000000000000001/workspaces/63289a172dc03cc436625464/projects/632aacee2dc03cc436625975/datasets/632aacee2dc03cc436625976/media/images/632c6eae2dc03cc436625a2a/display/full ',
        height: 480,
        width: 640,
    },
    name: '000000002006',
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/63289a172dc03cc436625464/projects/632aacee2dc03cc436625975/datasets/632aacee2dc03cc436625976/media/images/632c6eae2dc03cc436625a2a/display/thumb',
    type: 'image',
    upload_time: '2022-09-22T14:18:22.980000+00:00',
    uploader_id: 'admin@intel.com',
};

export const labelIDs = {
    normal: '632aacee2dc03cc43662597c',
    anomalous: '632aacee2dc03cc43662597d',
};

export const project = {
    creation_time: '2022-09-21T06:19:26.180000+00:00',
    creator_id: 'user@intel.com',
    datasets: [
        {
            creation_time: '2022-09-21T06:19:26.179000+00:00',
            id: '632aacee2dc03cc436625976',
            name: 'Dataset',
            use_for_training: true,
        },
    ],
    id: '632aacee2dc03cc436625975',
    name: 'Example Anomaly classification project',
    performance: {
        score: 0.24999999999999994,
        task_performances: [
            {
                score: {
                    value: 0.24999999999999994,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    pipeline: {
        connections: [
            {
                from: '632aacee2dc03cc436625973',
                to: '632aacee2dc03cc436625974',
            },
        ],
        tasks: [
            {
                id: '632aacee2dc03cc436625973',
                task_type: 'dataset',
                title: 'Dataset',
            },
            {
                id: '632aacee2dc03cc436625974',
                label_schema_id: '632aacee2dc03cc43662597f',
                labels: [
                    {
                        color: '#8bae46ff',
                        group: 'default - Anomaly classification',
                        hotkey: '',
                        id: labelIDs.normal,
                        is_anomalous: false,
                        is_empty: false,
                        name: 'Normal',
                        parent_id: null,
                    },
                    {
                        color: '#ff5662ff',
                        group: 'default - Anomaly classification',
                        hotkey: '',
                        id: labelIDs.anomalous,
                        is_anomalous: true,
                        is_empty: false,
                        name: 'Anomalous',
                        parent_id: null,
                    },
                ],
                task_type: 'anomaly_classification',
                title: 'Anomaly classification',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/63289a172dc03cc436625464/projects/632aacee2dc03cc436625975/thumbnail',
};
