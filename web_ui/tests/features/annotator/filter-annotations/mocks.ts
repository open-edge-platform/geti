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
export { project, annotatorUrl } from './../../../mocks/detection-classification/mocks';
export {
    project as segmentationProject,
    annotatorUrl as segmentationUrl,
    predictionAnnotationsResponse as segmentationPredictionsResponse,
} from './../../../mocks/segmentation/mocks';

const annotatorUrl =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/63283aedc80c9c686fd3b1e7/annotator/image/613a23866674c43ae7a777aa';

export const urlWithFilter =
    // eslint-disable-next-line max-len
    `${annotatorUrl}?annotations-filter=JTdCJUMyJUE4Y29uZGl0aW9uJUMyJUE4JUMyJUE4YW5kJUMyJUE4JUMyJUE4cnVsZXMlQzIlQTglN0MlN0IlQzIlQThmaWVsZCVDMiVBOCVDMiVBOExBQkVMX0lEJUMyJUE4JUMyJUE4aWQlQzIlQTglQzIlQTg0NTE1OGQwNS04MjcxLTQ5MTQtODU4NS0xYjNkMTM4YmEzMWYlQzIlQTglQzIlQThvcGVyYXRvciVDMiVBOCVDMiVBOElOJUMyJUE4JUMyJUE4dmFsdWUlQzIlQTglN0MlQzIlQTg2MzI4M2FlZGM4MGM5YzY4NmZkM2IxZjglQzIlQTglQzIlQTg2MzI4M2FlZGM4MGM5YzY4NmZkM2IxZmQlQzIlQTglQzMlQjclN0QlQzMlQjclN0Q%3D`;

export const annotationResponse = {
    annotation_state_per_task: [
        { state: 'annotated', task_id: '63d8cec1ac620f32e365aca1' },
        { state: 'annotated', task_id: '63d8cec1ac620f32e365aca3' },
    ],
    annotations: [
        {
            id: '42a249a2-8173-4a61-be5c-c9a74062121f',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#f15b85ff',
                    id: '63283aedc80c9c686fd3b1f9',
                    name: 'Hearts',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#9d3b1aff',
                    id: '63283aedc80c9c686fd3b1fb',
                    name: '7',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 221, type: 'RECTANGLE', width: 210, x: 295, y: 66 },
        },
        {
            id: '16bf946c-50ec-42c6-9257-f5c6478eda34',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#708541ff',
                    id: '63283aedc80c9c686fd3b1f8',
                    name: 'Spades',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#25a18eff',
                    id: '63283aedc80c9c686fd3b200',
                    name: 'J',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 140, type: 'RECTANGLE', width: 212, x: 38, y: 0 },
        },
        {
            id: 'a298312a-1b59-4415-9722-2c216a875536',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#708541ff',
                    id: '63283aedc80c9c686fd3b1f8',
                    name: 'Spades',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#80e9afff',
                    id: '63283aedc80c9c686fd3b201',
                    name: 'Q',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 160, type: 'RECTANGLE', width: 68, x: 0, y: 168 },
        },
        {
            id: '2beec505-085e-4ebb-8b2e-c20cf00353b7',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#f15b85ff',
                    id: '63283aedc80c9c686fd3b1f9',
                    name: 'Hearts',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#9b5de5ff',
                    id: '63283aedc80c9c686fd3b1fd',
                    name: '8',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 236, type: 'RECTANGLE', width: 223, x: 115, y: 296 },
        },
        {
            id: '652697a0-d7e1-43ac-97a6-7650a4346103',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#f15b85ff',
                    id: '63283aedc80c9c686fd3b1f9',
                    name: 'Hearts',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#80e9afff',
                    id: '63283aedc80c9c686fd3b201',
                    name: 'Q',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 241, type: 'RECTANGLE', width: 237, x: 371, y: 478 },
        },
        {
            id: '97845455-6099-482f-ba1d-189955a1c57e',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#f15b85ff',
                    id: '63283aedc80c9c686fd3b1f9',
                    name: 'Hearts',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#25a18eff',
                    id: '63283aedc80c9c686fd3b200',
                    name: 'J',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 227, type: 'RECTANGLE', width: 238, x: 528, y: 236 },
        },
        {
            id: '7844a16b-1c08-4ad5-9ad3-d745ebcb3dfe',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#cc94daff',
                    id: '63283aedc80c9c686fd3b1f6',
                    name: 'Clubs',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#9d3b1aff',
                    id: '63283aedc80c9c686fd3b1fb',
                    name: '7',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 78, type: 'RECTANGLE', width: 28, x: 836, y: 465 },
        },
        {
            id: '41ba3bfd-ea8b-4012-86ee-5dd89394b2c1',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#cc94daff',
                    id: '63283aedc80c9c686fd3b1f6',
                    name: 'Clubs',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#9b5de5ff',
                    id: '63283aedc80c9c686fd3b1fd',
                    name: '8',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.783000+00:00',
            shape: { height: 255, type: 'RECTANGLE', width: 195, x: 669, y: 636 },
        },
        {
            id: 'cefa4c9c-7093-42b4-a4dc-c8caaad26581',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#cc94daff',
                    id: '63283aedc80c9c686fd3b1f6',
                    name: 'Clubs',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#00f5d4ff',
                    id: '63283aedc80c9c686fd3b1fe',
                    name: '9',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.784000+00:00',
            shape: { height: 265, type: 'RECTANGLE', width: 249, x: 498, y: 887 },
        },
        {
            id: '6a5b3fe1-ea6b-402d-a973-998fb8429f1e',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#f15b85ff',
                    id: '63283aedc80c9c686fd3b1f9',
                    name: 'Hearts',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#548fadff',
                    id: '63283aedc80c9c686fd3b202',
                    name: 'K',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.784000+00:00',
            shape: { height: 248, type: 'RECTANGLE', width: 248, x: 195, y: 685 },
        },
        {
            id: '5ed6cf5d-ab8e-45a8-8579-3fe740a850b5',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#f15b85ff',
                    id: '63283aedc80c9c686fd3b1f9',
                    name: 'Hearts',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#00f5d4ff',
                    id: '63283aedc80c9c686fd3b1fe',
                    name: '9',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.784000+00:00',
            shape: { height: 244, type: 'RECTANGLE', width: 166, x: 0, y: 525 },
        },
        {
            id: '865b883f-1a33-460f-9a8a-c667dc7ab9a0',
            labels: [
                {
                    color: '#edb200ff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Card',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#f15b85ff',
                    id: '63283aedc80c9c686fd3b1f9',
                    name: 'Hearts',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
                {
                    color: '#e96115ff',
                    id: '63283aedc80c9c686fd3b203',
                    name: 'A',
                    probability: 1,
                    source: { model_id: null, model_storage_id: null, user_id: 'admin@intel.com' },
                },
            ],
            labels_to_revisit: [],
            modified: '2023-02-10T13:24:45.784000+00:00',
            shape: { height: 205, type: 'RECTANGLE', width: 250, x: 6, y: 947 },
        },
    ],
    id: '63e6459d6b398f3a6bc4be68',
    kind: 'annotation',
    labels_to_revisit_full_scene: [],
    media_identifier: { image_id: '63e0af766b398f3a6bc4aa6e', type: 'image' },
    modified: '2023-02-10T13:24:45.784000+00:00',
};
