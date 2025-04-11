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

import { SHAPE_TYPE_DTO } from '../../../src/core/annotations/dtos/annotation.interface';
import {
    AnnotationDTOWithLabelProperties as AnnotationDTO,
    LabelsWithNameAndColor as AnnotationLabelDTO,
} from '../../utils/annotation';

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

export const cardLabelId = '63283aedc80c9c686fd3b1f1';
export const detectionLabels = [
    {
        color: '#cc94daff',
        group: 'Default group root task',
        hotkey: '',
        id: cardLabelId,
        is_anomalous: false,
        is_empty: false,
        name: 'Card',
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

export const classificationLabels = [
    {
        color: '#edb200ff',
        group: 'Default group root task___Suit',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f6',
        is_anomalous: false,
        is_empty: false,
        name: 'Clubs',
        parent_id: cardLabelId,
    },
    {
        color: '#c9e649ff',
        group: 'Default group root task___Suit',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f8',
        is_anomalous: false,
        is_empty: false,
        name: 'Spades',
        parent_id: cardLabelId,
    },
    {
        color: '#9b5de5ff',
        group: 'Default group root task___Suit',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f9',
        is_anomalous: false,
        is_empty: false,
        name: 'Hearts',
        parent_id: cardLabelId,
    },
    {
        color: '#00a5cfff',
        group: 'Default group root task___Suit',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1fa',
        is_anomalous: false,
        is_empty: false,
        name: 'Diamonds',
        parent_id: cardLabelId,
    },
    {
        color: '#f7dab3ff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1fb',
        is_anomalous: false,
        is_empty: false,
        name: '7',
        parent_id: cardLabelId,
    },
    {
        color: '#5b69ffff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1fd',
        is_anomalous: false,
        is_empty: false,
        name: '8',
        parent_id: cardLabelId,
    },
    {
        color: '#548fadff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1fe',
        is_anomalous: false,
        is_empty: false,
        name: '9',
        parent_id: cardLabelId,
    },
    {
        color: '#81407bff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1ff',
        is_anomalous: false,
        is_empty: false,
        name: '10',
        parent_id: cardLabelId,
    },
    {
        color: '#ff5662ff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b200',
        is_anomalous: false,
        is_empty: false,
        name: 'J',
        parent_id: cardLabelId,
    },
    {
        color: '#80e9afff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b201',
        is_anomalous: false,
        is_empty: false,
        name: 'Q',
        parent_id: cardLabelId,
    },
    {
        color: '#e96115ff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b202',
        is_anomalous: false,
        is_empty: false,
        name: 'K',
        parent_id: cardLabelId,
    },
    {
        color: '#26518eff',
        group: 'Default group root task___Value',
        hotkey: '',
        id: '63283aedc80c9c686fd3b203',
        is_anomalous: false,
        is_empty: false,
        name: 'A',
        parent_id: cardLabelId,
    },
    {
        color: '#ba10a4ff',
        group: 'No class',
        hotkey: '',
        id: '63283aedc80c9c686fd3b204',
        is_anomalous: false,
        is_empty: true,
        name: 'No class',
        parent_id: cardLabelId,
    },
];

export const project = {
    creation_time: '2022-09-19T09:48:29.261000+00:00',
    creator_id: 'admin@intel.com',
    datasets: [
        {
            creation_time: '2022-09-19T09:48:29.259000+00:00',
            id: '63283aedc80c9c686fd3b1e7',
            name: 'Default dataset',
            use_for_training: true,
        },
    ],
    id: '63283aedc80c9c686fd3b1e6',
    name: 'Card detection classification',
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
    pipeline: {
        connections: [
            { from: '63283aedc80c9c686fd3b1e2', to: '63283aedc80c9c686fd3b1e3' },
            { from: '63283aedc80c9c686fd3b1e3', to: '63283aedc80c9c686fd3b1e4' },
            { from: '63283aedc80c9c686fd3b1e4', to: '63283aedc80c9c686fd3b1e5' },
        ],
        tasks: [
            { id: '63283aedc80c9c686fd3b1e2', task_type: 'dataset', title: 'Dataset' },
            {
                id: '63283aedc80c9c686fd3b1e3',
                label_schema_id: '63283aedc80c9c686fd3b1f5',
                labels: detectionLabels,
                task_type: 'detection',
                title: 'Detection',
            },
            { id: '63283aedc80c9c686fd3b1e4', task_type: 'crop', title: 'Crop' },
            {
                id: '6101254defba22ca453f11d1',
                label_schema_id: '63283aedc80c9c686fd3b206',
                labels: classificationLabels,
                task_type: 'classification',
                title: 'Classification',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/63230739c80c9c686fd3a7ce/projects/63283aedc80c9c686fd3b1e6/thumbnail',
};

const roi = { x: 0, y: 0, height: 907, width: 681 };
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

export const userAnnotationId = '6b3b8453-92a2-41ef-9725-63badb218501';
export const userAnnotationIdTwo = '6b3b8453-92a2-41ef-9725-63badb218502';
export const userDetectionAnnotationsResponse = {
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
            shape: { type: 'RECTANGLE', x: 0, y: 0, width: 600, height: 400 },
        },
    ],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'annotation',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    labels_to_revisit_full_scene: ['61387685df33ae8280c33d9d'],
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
};

export const userDetectionAnnotationsClassificationResponse = {
    ...userDetectionAnnotationsResponse,
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
                {
                    ...classificationLabels[0],
                    probability: 1,
                    source: {
                        user_id: 'default_user',
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
                {
                    ...classificationLabels[4],
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
            id: userAnnotationIdTwo,
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
                {
                    ...classificationLabels[1],
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
            shape: { type: 'RECTANGLE', ...roi, x: 200, y: 200 },
        },
    ],
};

export const predictionAnnotationId = userAnnotationId;
export const predictionAnnotationIdTwo = userAnnotationIdTwo;

export const predictionAnnotationsResponse = {
    annotations: [
        {
            id: predictionAnnotationId,
            labels: [
                {
                    ...detectionLabels[0],
                    probability: 0.87,
                    source: {
                        user_id: null,
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
                {
                    ...classificationLabels[0],
                    probability: 0.37,
                    source: {
                        user_id: null,
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
                {
                    ...classificationLabels[4],
                    probability: 0.54,
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
            id: predictionAnnotationIdTwo,
            labels: [
                {
                    ...detectionLabels[0],
                    probability: 0.97,
                    source: {
                        user_id: null,
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
                {
                    ...classificationLabels[1],
                    probability: 0.27,
                    source: {
                        user_id: null,
                        model_id: '61387685df33ae8280c347b2',
                        model_storage_id: '62387685df33ae8280c63a34',
                    },
                },
                {
                    ...classificationLabels[2],
                    probability: 0.24,
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
    ],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'prediction',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    maps: [
        {
            id: '6450b2eb6d89c127db4cc6dc',
            label_id: detectionLabels[0].id,
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

const source = {
    user_id: 'c74a4a38-2d7e-47b0-a5fd-27dd73679eff',
    model_id: null,
    model_storage_id: null,
};

const projectLabels = [...detectionLabels, ...classificationLabels];

const userLabel = (labelId: string): AnnotationLabelDTO => {
    const label = projectLabels.find(({ id }) => id === labelId);

    if (label === undefined) {
        throw new Error('Unkown label');
    }

    return {
        id: labelId,
        probability: 1,
        source,
        color: label.color,
        name: label.name,
    };
};

export const cardAnnotations: AnnotationDTO[] = [
    {
        id: '1faf1bd9-c910-4ade-a39c-174667628c47',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1f9'), // Hearts
            userLabel('63283aedc80c9c686fd3b1fd'), // 8
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 379, y: 33, width: 200, height: 217 },
        labels_to_revisit: [],
    },
    {
        id: '7dff6524-b273-4c3e-862b-5a1027b7c44c',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1fa'), // Diamonds
            userLabel('63283aedc80c9c686fd3b200'), // J
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 209, y: 205, width: 145, height: 205 },
        labels_to_revisit: [],
    },
    {
        id: '47a5a82f-c18d-4cdd-bc2f-18b6aeb31acf',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1f6'), // Clubs
            userLabel('63283aedc80c9c686fd3b1fe'), // 9
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 0, y: 139, width: 196, height: 210 },
        labels_to_revisit: [],
    },
    {
        id: '787e4c34-e7c6-4a4e-b902-228708f34eac',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1fa'), // Diamonds
            userLabel('63283aedc80c9c686fd3b1fd'), // 8
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 0, y: 441, width: 174, height: 242 },
        labels_to_revisit: [],
    },
    {
        id: '436c365c-edeb-4302-99e6-be6ce7cd82d0',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1f6'), // Clubs
            userLabel('63283aedc80c9c686fd3b1ff'), // 10
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 98, y: 749, width: 232, height: 171 },
        labels_to_revisit: [],
    },
    {
        id: '16a432fc-0e40-4ab2-99a8-0d63a0a488af',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1fa'), // Diamonds
            userLabel('63283aedc80c9c686fd3b201'), // Queen
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 197, y: 564, width: 163, height: 225 },
        labels_to_revisit: [],
    },
    {
        id: '37cbba92-1e0c-4556-a6c7-c56781be6167',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1f8'), // Spades
            userLabel('63283aedc80c9c686fd3b201'), // Queen
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 308, y: 356, width: 198, height: 236 },
        labels_to_revisit: [],
    },
    {
        id: 'f696a590-2f6c-41e7-9654-1fd8cfbf8bdd',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1f8'), // Spades
            userLabel('63283aedc80c9c686fd3b203'), // A
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 538, y: 267, width: 181, height: 197 },
        labels_to_revisit: [],
    },
    {
        id: 'c70e25c8-3ad4-4560-a84e-05df53f6c5b9',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1f9'), // Hearts
            userLabel('63283aedc80c9c686fd3b201'), // Queen
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 537, y: 391, width: 183, height: 245 },
        labels_to_revisit: [],
    },
    {
        id: '6c1fe0e8-e515-4a33-a18f-3f7fecb4355c',
        modified: '2024-02-13T17:39:52.544000+00:00',
        labels: [
            userLabel(cardLabelId), // Card
            userLabel('63283aedc80c9c686fd3b1f6'), // Clubs
            userLabel('63283aedc80c9c686fd3b201'), // Queen
        ],
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 427, y: 637, width: 224, height: 264 },
        labels_to_revisit: [],
    },
];

export const modelGroups = [
    {
        id: '66602ad1544cd34d1d42ab0c',
        name: 'MobileNetV2-ATSS',
        model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
        task_id: '66602ad1544cd34d1d42ab0b',
        models: [
            {
                id: '66602cb0256510e337189c43',
                name: 'MobileNetV2-ATSS',
                creation_date: '2024-06-05T09:15:28.214000+00:00',
                score_up_to_date: true,
                active_model: true,
                size: 28318215,
                performance: {
                    score: 0.9047619047619045,
                },
                label_schema_in_sync: true,
                version: 1,
            },
        ],
    },
    {
        id: '66602ad1544cd34d1d42ab0f',
        name: 'EfficientNet-B0',
        model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
        task_id: '66602ad1544cd34d1d42ab0e',
        models: [
            {
                id: '66602cba1f4b50ba0b7fe1ea',
                name: 'EfficientNet-B0',
                creation_date: '2024-06-05T09:15:38.711000+00:00',
                score_up_to_date: true,
                active_model: true,
                size: 32516949,
                performance: {
                    score: 0.125,
                },
                label_schema_in_sync: true,
                version: 1,
            },
        ],
    },
];
