// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

const roi = { x: 0, y: 0, width: 600, height: 400 };

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3ba33/datasets/6101254defba22ca453f11d0/annotator/image/613a23866674c43ae7a777bb';

const getMockedMedia = (name: string, id?: string) => {
    return {
        id: id ?? '613a23866674c43ae7a777bb',
        uploader_id: 'user@company.com',
        media_information: {
            display_url: '/v2/projects/61012cdb1d38a5e71ef3ba33/media/images/613a23866674c43ae7a777bb/display/full',
            height: roi.height,
            width: roi.width,
        },
        name,
        annotation_state_per_task: [],
        thumbnail: '/v2/projects/61012cdb1d38a5e71ef3ba33/media/images/613a23866674c43ae7a777bb/display/thumb',
        type: 'image',
        upload_time: '2021-06-29T17:13:44.719000+00:00',
    };
};
export const media = getMockedMedia('Course completion');

export const project = {
    creation_time: '2021-07-28T09:37:17.319000+00:00',
    creator_id: 'Example user',
    datasets: [
        {
            id: '6101254defba22ca453f11d0',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2022-09-14T12:35:53.070000+00:00',
        },
    ],
    id: '61012cdb1d38a5e71ef3ba33',
    name: 'Example detection project',
    pipeline: {
        connections: [{ from: '6101254defba22ca453f11d0', to: '6101254defba22ca453f11ce' }],
        tasks: [
            { id: '6101254defba22ca453f11ce', task_type: 'dataset', title: 'Dataset' },
            {
                id: '6101254defba22ca453f11d1',
                label_schema_id: '6101254defba22ca453f11c2',
                labels: [
                    {
                        color: '#cc94daff',
                        group: 'Detection',
                        hotkey: '',
                        id: '63283aedc80c9c686fd3b1f1',
                        is_anomalous: false,
                        is_empty: false,
                        name: 'Fish',
                        parent_id: null,
                    },
                ],
                task_type: 'rotated_detection',
                title: 'Sample detection task',
            },
        ],
    },
    performance: {
        score: 0.35,
        task_performances: [
            {
                score: {
                    value: 0.35,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/000000000000000000000001/workspaces/6101254defba22ca453f11c2/projects/61012cdb1d38a5e71ef3ba33/thumbnail',
};
