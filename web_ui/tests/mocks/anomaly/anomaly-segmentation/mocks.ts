// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
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
    name: 'Example Anomaly segmentation project',
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
                task_type: 'anomaly_segmentation',
                title: 'Sample anomaly segmentation',
            },
        ],
    },
    performance: {
        score: 0.7,
        global_score: 0.7,
        local_score: 0.3,
        task_performances: [
            {
                score: {
                    value: 0.7,
                    metric_type: 'accuracy',
                },
                global_score: {
                    value: 0.7,
                    metric_type: 'accuracy',
                },
                local_score: {
                    value: 0.3,
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
