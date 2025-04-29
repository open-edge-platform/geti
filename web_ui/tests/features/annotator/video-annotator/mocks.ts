// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SHAPE_TYPE_DTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { AnnotationDTOWithLabelProperties as AnnotationDTO } from '../../../utils/annotation';
import {
    detectionLabels,
    project,
} from './../../../mocks/detection-classification/fish-detection-classification-project';

export { project };

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/63283aedc80c9c686fd3b1e7/annotator/video/613a23866674c43ae7a777ab/0';

export const videoMediaItem = {
    annotation_state_per_task: [
        {
            state: 'partially_annotated',
            task_id: '638ef2aa765959d262ee76a2',
        },
        {
            state: 'partially_annotated',
            task_id: '638ef2aa765959d262ee76a4',
        },
    ],
    id: '638ef364765959d262ee829d',
    media_information: {
        display_url:
            // eslint-disable-next-line max-len
            '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/637be0abfc0fc8ef2eaa2272/projects/638ef2aa765959d262ee76a5/datasets/638ef2aa765959d262ee76a6/media/videos/638ef364765959d262ee829d/display/stream',
        duration: 60,
        frame_count: 3600,
        frame_rate: 60,
        frame_stride: 60,
        height: 720,
        width: 1280,
    },
    name: 'fish_120',
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/637be0abfc0fc8ef2eaa2272/projects/638ef2aa765959d262ee76a5/datasets/638ef2aa765959d262ee76a6/media/videos/638ef364765959d262ee829d/display/thumb',
    type: 'video',
    upload_time: '2022-12-06T07:46:45.237000+00:00',
    uploader_id: 'admin@intel.com',
};

const userAnnotationId = '6b3b8453-92a2-41ef-9725-63badb218504';
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
            shape: { type: 'RECTANGLE', x: 0, y: 0, height: 720, width: 1280 },
        },
    ],
    id: '6138afea3b7b11505c43f2c0',
    kind: 'annotation',
    media_identifier: { image_id: '6138af293b7b11505c43f2bc', type: 'image' },
    modified: '2021-09-08T12:43:22.290000+00:00',
    labels_to_revisit_full_scene: ['61387685df33ae8280c33d9d'],
    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'to_revisit' }],
};

export const frameAnnotations: AnnotationDTO[] = [
    {
        id: 'annotation-0-0',
        shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 100, y: 100, width: 100, height: 100 },
        labels: [
            {
                id: '63283aedc80c9c686fd3b1f1',
                name: 'Fish',
                color: '#cc94daff',
                probability: 1,
                hotkey: '',
                source: { model_id: null, model_storage_id: null, user_id: 'user' },
            },
            {
                id: 'YellowFish',
                name: 'Yellow Fish',
                color: '#c9e649ff',
                probability: 1,
                hotkey: '',
                source: { model_id: null, model_storage_id: null, user_id: 'user' },
            },
        ],
        labels_to_revisit: [],
    },
];

export const FIXED_DTO_SHAPE = { type: SHAPE_TYPE_DTO.RECTANGLE, x: 100, y: 100, width: 200, height: 200 };
export const USER_SOURCE = { model_id: null, model_storage_id: null, user_id: 'user' };
export const MODEL_SOURCE = { model_id: 'fish-model', model_storage_id: 'some-storage', user_id: null };
export const VIDEO_PAGINATION_PROPERTIES = {
    end_frame: 3600,
    requested_end_frame: 3600,
    start_frame: 0,
    total_count: 3600,
    total_requested_count: 0,
};

export const mockVideoAnnotations = (frameIndex: number, label: string) => {
    return {
        ...userAnnotationsResponse,
        media_identifier: {
            type: 'video_frame',
            video_id: '613a23866674c43ae7a777ab',
            frame_index: `${frameIndex}`,
        },
        annotations: [
            {
                id: `annotation-${frameIndex}`,
                shape: FIXED_DTO_SHAPE,
                labels: [
                    {
                        id: '63283aedc80c9c686fd3b1f1',
                        name: 'Fish',
                        color: '#cc94daff',
                        probability: 1.0,
                        source: USER_SOURCE,
                    },
                    {
                        id: label,
                        name: label,
                        color: '#cc94daff',
                        probability: 1.0,
                        source: USER_SOURCE,
                    },
                ],
                labels_to_revisit: [],
            },
        ],
    };
};

export const mockVideoPredictions = (frameIndex: number, label: string) => {
    return {
        ...userAnnotationsResponse,
        media_identifier: {
            type: 'video_frame',
            video_id: '613a23866674c43ae7a777ab',
            frame_index: `${frameIndex}`,
        },
        annotations: [
            {
                id: `annotation-${frameIndex}`,
                shape: FIXED_DTO_SHAPE,
                labels: [
                    {
                        id: '63283aedc80c9c686fd3b1f1',
                        name: 'Fish',
                        color: '#cc94daff',
                        probability: 0.33,
                        source: MODEL_SOURCE,
                    },
                    {
                        id: label,
                        name: label,
                        color: '#cc94daff',
                        probability: 0.13,
                        source: MODEL_SOURCE,
                    },
                ],
                labels_to_revisit: [],
            },
        ],
    };
};
