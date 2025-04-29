// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { labelIDs } from './../../../../mocks/anomaly/anomaly-classification/mocks';

export { project } from './../../../../mocks/anomaly/anomaly-classification/mocks';

export const videoMediaItem = {
    id: '613a23866674c43ae7a777ab',
    media_information: {
        display_url:
            // eslint-disable-next-line max-len
            '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61376cf8c0e392f0c4efb2bb/projects/6139eab61e3343cd22a41a66/datasets/6139eab61e3343cd22a41a65/media/videos/6139ec7555f78343bad38d2b/display/stream',
        duration: 30,
        frame_count: 901,
        frame_stride: 30,
        frame_rate: 30,
        height: 270,
        width: 480,
    },
    name: 'dummy_video',
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61376cf8c0e392f0c4efb2bb/projects/6139eab61e3343cd22a41a66/datasets/6139eab61e3343cd22a41a65/media/images/613a23866674c43ae7a777ab/display/thumb',
    type: 'video',
    annotation_state_per_task: [
        {
            task_id: '61012cdb1d38a5e71ef3bafd',
            state: 'annotated',
        },
    ],
    upload_time: '2021-09-09T15:08:54.118000+00:00',
};

export const videoAnnotations = {
    video_annotation_properties: {
        end_frame: 901,
        start_frame: 0,
        requested_end_frame: null,
        requested_start_frame: 0,
        total_count: 901,
        total_requested_count: 901,
    },
    video_annotations: new Array(901).fill(0).map((_, index) => ({
        annotationStatePerTask: [
            {
                task_id: '61012cdb1d38a5e71ef3bafd',
                state: 'annotated',
            },
        ],
        annotations: [
            {
                id: '00000000000' + Math.random().toString(16).substring(2),
                labels: [
                    {
                        id: labelIDs.normal,
                        probability: 1,
                        source: {
                            model_id: null,
                            model_storage_id: null,
                            user: 'admin@intel.com',
                        },
                    },
                ],
                labels_to_revisit: [],
                modiifed: '2022-12-12T16:33:20.436000+00:00',
                shape: {
                    type: 'rectangle',
                    height: 270,
                    width: 480,
                    x: 0,
                    y: 0,
                },
            },
        ],
        id: '00000000000' + Math.random().toString(16).substring(2),
        kind: 'annotation',
        labels_to_revisit_full_scene: [],
        media_identifier: {
            frame_index: index,
            type: 'video_frame',
            video_id: '613a23866674c43ae7a777ab',
        },
        modified: '2022-12-12T16:33:20.436000+00:00',
    })),
};
