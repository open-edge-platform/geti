// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/6332b40a2dc03cc436625b63/datasets/6332b40a2dc03cc436625b64/annotator/image/6332b4482dc03cc436625ba6';

export const project = {
    creation_time: '2022-09-27T08:27:54.782000+00:00',
    creator_id: 'admin@intel.com',
    datasets: [
        {
            creation_time: '2022-09-27T08:27:54.780000+00:00',
            id: '6332b40a2dc03cc436625b64',
            name: 'Dataset',
            use_for_training: true,
        },
    ],
    id: '6332b40a2dc03cc436625b63',
    name: 'Example Anomaly detection project',
    performance: {
        score: 0.0,
        global_score: 0.0,
        local_score: 0.2,
        task_performances: [
            {
                score: {
                    value: 0.0,
                    metric_type: 'accuracy',
                },
                global_score: {
                    value: 0.0,
                    metric_type: 'accuracy',
                },
                local_score: {
                    value: 0.2,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    pipeline: {
        connections: [{ from: '6332b40a2dc03cc436625b61', to: '6332b40a2dc03cc436625b62' }],
        tasks: [
            { id: '6332b40a2dc03cc436625b61', task_type: 'dataset', title: 'Dataset' },
            {
                id: '6332b40a2dc03cc436625b62',
                label_schema_id: '6332b40a2dc03cc436625b6d',
                labels: [
                    {
                        color: '#8bae46ff',
                        group: 'default - Anomaly detection',
                        hotkey: '',
                        id: '6332b40a2dc03cc436625b6a',
                        is_anomalous: false,
                        is_empty: false,
                        name: 'Normal',
                        parent_id: null,
                    },
                    {
                        color: '#ff5662ff',
                        group: 'default - Anomaly detection',
                        hotkey: '',
                        id: '6332b40a2dc03cc436625b6b',
                        is_anomalous: true,
                        is_empty: false,
                        name: 'Anomalous',
                        parent_id: null,
                    },
                ],
                task_type: 'anomaly_detection',
                title: 'Anomaly detection',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/63289a172dc03cc436625464/projects/6332b40a2dc03cc436625b63/thumbnail',
};

export const media = {
    annotation_state_per_task: [
        {
            state: 'partially_annotated',
            task_id: '6332b40a2dc03cc436625b62',
        },
    ],
    id: '6332b4482dc03cc436625ba6',
    media_information: {
        display_url:
            // eslint-disable-next-line max-len
            '/api/v1/organizations/000000000000000000000001/workspaces/63289a172dc03cc436625464/projects/6332b40a2dc03cc436625b63/datasets/6332b40a2dc03cc436625b64/media/images/6332b4482dc03cc436625ba6/display/full ',
        height: 1373,
        width: 2048,
    },
    name: '12574161474_2fe29a1cf0_k-1 - Copy - Copy',
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/63289a172dc03cc436625464/projects/6332b40a2dc03cc436625b63/datasets/6332b40a2dc03cc436625b64/media/images/6332b4482dc03cc436625ba6/display/thumb',
    type: 'image',
    upload_time: '2022-09-27T08:28:56.453000+00:00',
    uploader_id: 'admin@intel.com',
};
