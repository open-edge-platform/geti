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

import { OpenApiResponseBody } from '../../../../src/core/server/types';

export const anomalyLabels = [
    {
        color: '#8bae46ff',
        group: 'default - Anomaly classification',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f8',
        is_anomalous: false,
        is_empty: false,
        name: 'Normal',
        parent_id: null,
    },
    {
        color: '#ff5662ff',
        group: 'default - Anomaly classification',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f6',
        is_anomalous: true,
        is_empty: false,
        name: 'Anomalous',
        parent_id: null,
    },
];

export const project: OpenApiResponseBody<'GetProjectInfo'> = {
    creation_time: '2022-09-25T11:05:26.666000+00:00',
    creator_id: 'admin@intel.com',
    datasets: [
        {
            creation_time: '2022-09-25T11:05:26.663000+00:00',
            id: '633035f6c80c9c686fd3bd84',
            name: 'Dataset',
            use_for_training: true,
        },
    ],
    storage_info: {},
    id: '633035f6c80c9c686fd3bd83',
    name: 'AC Test',
    performance: {
        score: null,
        task_performances: [
            {
                score: null,
                task_id: 'task-id',
            },
        ],
    },
    pipeline: {
        connections: [{ from: '633035f6c80c9c686fd3bd81', to: '633035f6c80c9c686fd3bd82' }],
        tasks: [
            { id: '633035f6c80c9c686fd3bd81', task_type: 'dataset', title: 'Dataset' },
            {
                id: '60db493fd20945a0046f56d2',
                label_schema_id: '633035f6c80c9c686fd3bd8d',
                labels: anomalyLabels,
                task_type: 'anomaly_classification',
                title: 'Anomaly classification',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/63230739c80c9c686fd3a7ce/projects/633035f6c80c9c686fd3bd83/thumbnail',
};
