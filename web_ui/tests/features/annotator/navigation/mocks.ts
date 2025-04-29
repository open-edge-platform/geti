// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { classificationLabels, detectionLabels } from '../../../mocks/detection-classification/mocks';

export const detectionAnnotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator/image/1';

export const detectionProject = {
    creation_time: '2022-09-19T09:48:29.261000+00:00',
    creator_id: 'admin@intel.com',
    datasets: [
        {
            id: '6101254defba22ca453f11cc',
            name: 'Test Dataset',
            creation_time: '2021-07-28T09:48:29.261000+00:00',
            use_for_training: true,
        },
    ],
    id: '61012cdb1d38a5e71ef3baf9',
    name: 'test',
    performance: {
        score: 0.0,
        task_performances: [
            {
                score: {
                    value: 0.0,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    pipeline: {
        connections: [{ from: '61012cdb1d38a5e71ef3bafa', to: '61012cdb1d38a5e71ef3bafb' }],
        tasks: [
            { id: '61012cdb1d38a5e71ef3bafa', task_type: 'dataset', name: 'Dataset' },
            {
                id: '61012cdb1d38a5e71ef3bafb',
                task_type: 'detection',
                name: 'Detection',
                labels: [],
                label_schema_id: {},
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/61012cdb1d38a5e71ef3baf9/thumbnail',
};

export const detectionChainProject = {
    creation_time: '2022-09-19T09:48:29.261000+00:00',
    creator_id: 'admin@intel.com',
    datasets: [
        {
            id: '6101254defba22ca453f11cc',
            name: 'Test Dataset',
            creation_time: '2021-07-28T09:48:29.261000+00:00',
            use_for_training: true,
        },
    ],
    id: '61012cdb1d38a5e71ef3baf9',
    name: 'test',
    performance: {
        score: 0.0,
        task_performances: [
            {
                score: {
                    value: 0.0,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    pipeline: {
        connections: [
            { from: '61012cdb1d38a5e71ef3bafa', to: '61012cdb1d38a5e71ef3bafb' },
            { from: '61012cdb1d38a5e71ef3bafb', to: '61012cdb1d38a5e71ef3bafc' },
            { from: '61012cdb1d38a5e71ef3bafc', to: '61012cdb1d38a5e71ef3bafd' },
            { from: '61012cdb1d38a5e71ef3bafd', to: '61012cdb1d38a5e71ef3bafe' },
        ],
        tasks: [
            { id: '61012cdb1d38a5e71ef3bafa', task_type: 'dataset', title: 'Dataset' },
            {
                id: '61012cdb1d38a5e71ef3bafb',
                task_type: 'detection',
                title: 'Detection',
                labels: detectionLabels,
                label_schema_id: '61012cdb1d38a5e71ef3baf9',
            },
            { id: '61012cdb1d38a5e71ef3bafc', task_type: 'crop', title: 'Crop' },
            {
                id: '61012cdb1d38a5e71ef3bafd',
                label_schema_id: '61012cdb1d38a5e71ef3baf9',
                labels: classificationLabels,
                task_type: 'classification',
                title: 'Classification',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/61012cdb1d38a5e71ef3baf9/thumbnail',
};

const roi = { x: 0, y: 0, width: 600, height: 400 };

export const activeSet = {
    active_set: [
        {
            id: '1',
            media_information: {
                display_url:
                    // eslint-disable-next-line max-len
                    'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/60d3549a3e6080a926e5ef12/datasets/6101254defba22ca453f11cc/media/images/1/display/full',
                height: roi.height,
                width: roi.width,
                size: 123456,
            },
            dataset_id: '6101254defba22ca453f11cc',
            name: 'Image 1',
            state: 'to_revisit',
            thumbnail:
                // eslint-disable-next-line max-len
                'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/60d3549a3e6080a926e5ef12/datasets/6101254defba22ca453f11cc/media/images/1/display/thumb',
            type: 'image',
            upload_time: '2021-07-28T09:48:29.261000+00:00',
        },
        {
            id: '3',
            active_frames: [30, 60],
            media_information: {
                display_url:
                    // eslint-disable-next-line max-len
                    'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/60d3549a3e6080a926e5ef12/datasets/6101254defba22ca453f11cc/media/videos/3/display/stream',
                duration: 2,
                frame_count: 60,
                frame_rate: 30,
                frame_stride: 30,
                size: 12345,
                height: roi.height,
                width: roi.width,
            },
            dataset_id: '6101254defba22ca453f11cc',
            name: 'Video 1',
            state: 'to_revisit',
            thumbnail:
                // eslint-disable-next-line max-len
                'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/60d3549a3e6080a926e5ef12/datasets/6101254defba22ca453f11cc/media/videos/3/display/thumb',
            type: 'video',
            upload_time: '2021-07-28T09:48:29.261000+00:00',
        },
        {
            id: '4',
            media_information: {
                display_url:
                    // eslint-disable-next-line max-len
                    'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/60d3549a3e6080a926e5ef12/datasets/6101254defba22ca453f11cc/media/images/4/display/full',
                height: roi.height,
                width: roi.width,
                size: 123456,
            },
            dataset_id: '6101254defba22ca453f11cc',
            name: 'Image 4',
            state: 'to_revisit',
            thumbnail:
                // eslint-disable-next-line max-len
                'api/v1/organizations/000000000000000000000001/workspaces/61012cdb1d38a5e71ef3baf9/projects/60d3549a3e6080a926e5ef12/datasets/6101254defba22ca453f11cc/media/images/4/display/thumb',
            type: 'image',
            upload_time: '2021-07-28T09:48:29.261000+00:00',
        },
    ],
};

export const getMedia = (id: string) => ({
    id,
    uploader_id: 'user@company.com',
    media_information: {
        display_url: `/v2/projects/60d3549a3e6080a926e5ef12/media/images/${id}/display/full`,
        height: roi.height,
        width: roi.width,
    },
    name: `Image ${id}`,
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
    thumbnail: `/v2/projects/60d3549a3e6080a926e5ef12/media/images/${id}/display/thumb`,
    type: 'image',
    upload_time: '2021-06-29T17:13:44.719000+00:00',
});

export const getVideoMedia = (id: string) => ({
    id,
    uploader_id: 'user@company.com',
    media_information: {
        display_url: `/v2/projects/60d3549a3e6080a926e5ef12/media/videos/${id}/display/stream`,
        duration: 2,
        frame_count: 60,
        frame_rate: 30,
        frame_stride: 30,
        height: roi.height,
        width: roi.width,
    },
    name: `Video ${id}`,
    thumbnail: `/v2/projects/60d3549a3e6080a926e5ef12/media/videos/${id}/display/thumb`,
    type: 'video',
    upload_time: '2021-06-29T17:13:44.719000+00:00',
});

export const detectionAnnotations = {
    annotations: [
        {
            id: '613a238234ab43ae7a712aa',
            labels: [
                {
                    color: '#cc94daff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Object',
                    probability: 1.0,
                    source: {
                        user_id: 'user@company.com',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-06-29T17:13:43.719000+00:00',
            shape: {
                type: 'RECTANGLE',
                x: 100,
                y: 100,
                width: 100,
                height: 100,
            },
        },
        {
            id: '613a238234ab43ae7a712ab',
            labels: [
                {
                    color: '#cc94daff',
                    id: '63283aedc80c9c686fd3b1f1',
                    name: 'Object',
                    probability: 1.0,
                    source: {
                        user_id: 'user@company.com',
                        model_id: null,
                        model_storage_id: null,
                    },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-06-29T17:13:44.719000+00:00',
            shape: {
                type: 'RECTANGLE',
                x: 400,
                y: 100,
                width: 100,
                height: 100,
            },
        },
    ],
    id: '613a23866674c43ae7a777aa',
    kind: 'annotation',
    media_identifier: { image_id: '1', type: 'image' },
    modified: '2021-06-29T17:13:44.719000+00:00',
    labels_to_revisit_full_scene: [],
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
};

export const noPredictionAnnotations = {
    annotations: [],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'prediction',
    media_identifier: { frame_index: 0, type: 'video_frame', video_id: '3' },
    modified: '2021-09-07T09:50:34.000Z',
    maps: [],
};
