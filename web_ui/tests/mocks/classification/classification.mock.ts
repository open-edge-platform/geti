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
    name: 'Example classification project',
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
                task_type: 'classification',
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
