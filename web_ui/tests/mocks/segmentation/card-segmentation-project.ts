// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

export const cardLabelId = '6101254defba22ca453f11c6';
export const emptyLabelId = '6101254defba22ca453f11ca';

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
                        color: '#c9e649ff',
                        group: 'default - Instance Segmentation',
                        hotkey: 'ctrl+1',
                        id: cardLabelId,
                        is_empty: false,
                        is_anomalous: false,
                        name: 'Card',
                    },
                    {
                        color: '#7ada55ff',
                        group: 'Empty',
                        hotkey: 'ctrl+0',
                        id: emptyLabelId,
                        is_empty: true,
                        is_anomalous: false,
                        name: 'Empty',
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
        height: 907,
        width: 681,
    },
    name: 'Course completion',
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

export const cards = [
    {
        id: '5954b7a0-9b27-4fc1-ae96-e79ae63b6f1c',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 719, y: 454 },
                { x: 719, y: 616 },
                { x: 702, y: 634 },
                { x: 689, y: 627 },
                { x: 562, y: 475 },
                { x: 566, y: 464 },
                { x: 661, y: 391 },
            ],
        },
    },
    {
        id: '46d66acf-5bf5-42b2-9d78-8a3945f61598',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 719, y: 307 },
                { x: 718, y: 354 },
                { x: 693, y: 420 },
                { x: 661, y: 389 },
                { x: 633, y: 411 },
                { x: 570, y: 461 },
                { x: 538, y: 453 },
                { x: 606, y: 267 },
            ],
        },
    },
    {
        id: '5a4073aa-e735-447e-9c1e-edeb6abbab62',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 578, y: 198 },
                { x: 462, y: 249 },
                { x: 379, y: 80 },
                { x: 493, y: 33 },
            ],
        },
    },
    {
        id: '366190f8-b88b-4889-8233-8f0b750dda28',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 195, y: 245 },
                { x: 119, y: 348 },
                { x: 0, y: 269 },
                { x: 0, y: 189 },
                { x: 39, y: 140 },
            ],
        },
    },
    {
        id: '0ed18510-5e22-4c6a-be85-97ab6d780c1f',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 172, y: 485 },
                { x: 92, y: 682 },
                { x: 0, y: 647 },
                { x: 0, y: 549 },
                { x: 49, y: 441 },
            ],
        },
    },
    {
        id: 'c5c83be5-d280-4d95-968a-567ddd3427f1',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 352, y: 213 },
                { x: 338, y: 408 },
                { x: 210, y: 399 },
                { x: 224, y: 206 },
            ],
        },
    },
    {
        id: '724af16a-0d1c-4050-ab19-d9ed5d8adb73',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 505, y: 403 },
                { x: 431, y: 591 },
                { x: 307, y: 537 },
                { x: 387, y: 355 },
            ],
        },
    },
    {
        id: 'cf9a5139-93b5-48a7-9782-15407f3386ee',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 357, y: 741 },
                { x: 360, y: 782 },
                { x: 320, y: 787 },
                { x: 312, y: 746 },
                { x: 214, y: 758 },
                { x: 198, y: 618 },
                { x: 200, y: 583 },
                { x: 332, y: 563 },
            ],
        },
    },
    {
        id: 'e502733c-1201-4230-992c-319b8b7bb2e4',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 328, y: 868 },
                { x: 325, y: 893 },
                { x: 178, y: 914 },
                { x: 111, y: 916 },
                { x: 97, y: 773 },
                { x: 312, y: 746 },
            ],
        },
    },
    {
        id: '2304447c-9573-4e63-ab42-321ab7526069',
        labels: [{ id: cardLabelId, probability: 1.0, source: userSource }],
        shape: {
            type: 'POLYGON',
            points: [
                { x: 650, y: 706 },
                { x: 550, y: 900 },
                { x: 427, y: 826 },
                { x: 529, y: 638 },
            ],
        },
    },
];
