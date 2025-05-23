// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { rest } from 'msw';

import { apiRequestUrl } from '../../../../../packages/core/src/services/test-utils';
import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { server } from '../../../annotations/services/test-utils';
import { API_URLS } from '../../../services/urls';
import { MEDIA_TYPE } from '../../base-media.interface';
import { MEDIA_ANNOTATION_STATUS } from '../../base.interface';
import { ImageIdentifier } from '../../image.interface';
import { VideoFrameIdentifier } from '../../video.interface';
import { createApiMediaService } from './api-media-service';

const taskId = '6525fabec389293789c214ab';

const activeMediaResponse = () => {
    return {
        active_set: [
            {
                active_frames: [3360, 3300],
                id: '6103b96e2360313e324963f2',
                media_information: {
                    display_url:
                        '/api/v1/workspaces/61039c80bd1cde3821dcfca6/projects/61039c81bd1cde3821dcfcad/datasets/dummy/media/videos/6103b96e2360313e324963f2/display/stream',
                    duration: 95,
                    frame_count: 5700,
                    frame_stride: 60,
                    frame_rate: 60,
                    height: 1920,
                    width: 1080,
                },
                annotation_state_per_task: [
                    {
                        task_id: taskId,
                        state: MEDIA_ANNOTATION_STATUS.NONE,
                    },
                ],
                name: 'VID_20210209_160431',
                state: MEDIA_ANNOTATION_STATUS.NONE,
                thumbnail:
                    '/api/v1/workspaces/61039c80bd1cde3821dcfca6/projects/61039c81bd1cde3821dcfcad/datasets/dummy/media/videos/6103b96e2360313e324963f2/display/thumb',
                type: 'video',
                upload_time: '2021-07-30T08:33:50.399',
            },
            {
                id: '61039cccbd1cde3821dcfcb2',
                media_information: {
                    display_url:
                        '/api/v1/workspaces/61039c80bd1cde3821dcfca6/projects/61039c81bd1cde3821dcfcad/datasets/dummy/media/images/61039cccbd1cde3821dcfcb2/display/full ',
                    height: 1599,
                    width: 899,
                },
                annotation_state_per_task: [
                    {
                        task_id: taskId,
                        state: MEDIA_ANNOTATION_STATUS.NONE,
                    },
                ],
                name: 'IMG_20201020_111432',
                state: MEDIA_ANNOTATION_STATUS.NONE,
                thumbnail:
                    '/api/v1/workspaces/61039c80bd1cde3821dcfca6/projects/61039c81bd1cde3821dcfcad/datasets/dummy/media/images/61039cccbd1cde3821dcfcb2/display/thumb',
                type: 'image',
                upload_time: '2021-07-30T08:33:50.399',
            },
        ],
    };
};

describe('API media service', () => {
    const datasetIdentifier = getMockedDatasetIdentifier();

    const mediaService = createApiMediaService();

    it('gets a single media item', async () => {
        const response = {
            id: '60b609ead036ba4566726c84',
            media_information: {
                display_url: '/v2/projects/60b609e0d036ba4566726c7f/media/images/60b609ead036ba4566726c84/display/full',
                height: 800,
                width: 600,
            },
            annotation_state_per_task: [],
            name: 'IMG_20201020_111432',
            state: MEDIA_ANNOTATION_STATUS.NONE,
            thumbnail: '/v2/projects/60b609e0d036ba4566726c7f/media/images/60b609ead036ba4566726c84/display/thumb',
            type: 'image',
            upload_time: '2021-06-01T10:20:26.411',
        };

        const mediaIdentifier = { type: MEDIA_TYPE.IMAGE, imageId: '60b609ead036ba4566726c84' } as const;
        const mediaUrl = API_URLS.MEDIA_ITEM(datasetIdentifier, mediaIdentifier);
        server.use(rest.get(apiRequestUrl(mediaUrl), (_req, res, ctx) => res(ctx.json(response))));

        const mediaItem = await mediaService.getMediaItem(datasetIdentifier, mediaIdentifier);

        expect(mediaItem).toEqual({
            identifier: mediaIdentifier,
            name: 'IMG_20201020_111432',
            src: API_URLS.MEDIA_ITEM_SRC(datasetIdentifier, mediaIdentifier),
            thumbnailSrc: API_URLS.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, mediaIdentifier),
            uploadTime: '2021-06-01T10:20:26.411',
            annotationStatePerTask: [],
            metadata: {
                height: 800,
                width: 600,
            },
            status: MEDIA_ANNOTATION_STATUS.NONE,
        });
    });

    it('gets a single video frame', async () => {
        const response = {
            id: '610b8d0e667b9b8a6641eb79',
            media_information: {
                display_url:
                    '/api/v1/workspaces/610aacd9667b9b8a6641e9e2/projects/610aacd9667b9b8a6641e9fa/datasets/dummy/media/videos/610b8d0e667b9b8a6641eb79/display/stream',
                duration: 95,
                frame_count: 5700,
                frame_stride: 60,
                frame_rate: 60,
                height: 1920,
                width: 1080,
            },
            annotation_state_per_task: [
                {
                    task_id: taskId,
                    state: MEDIA_ANNOTATION_STATUS.NONE,
                },
            ],
            name: 'VID_20210209_160431',
            state: MEDIA_ANNOTATION_STATUS.NONE,
            thumbnail:
                '/api/v1/workspaces/610aacd9667b9b8a6641e9e2/projects/610aacd9667b9b8a6641e9fa/datasets/dummy/media/videos/610b8d0e667b9b8a6641eb79/display/thumb',
            type: 'video',
            upload_time: '2021-08-05T07:02:38.182000+00:00',
        };

        const mediaIdentifier = {
            type: MEDIA_TYPE.VIDEO_FRAME,
            videoId: '610b8d0e667b9b8a6641eb79',
            frameNumber: 0,
        } as const;
        const videoIdentifier = {
            type: MEDIA_TYPE.VIDEO,
            videoId: '610b8d0e667b9b8a6641eb79',
        } as const;
        const mediaUrl = API_URLS.MEDIA_ITEM(datasetIdentifier, videoIdentifier);
        server.use(rest.get(apiRequestUrl(mediaUrl), (_req, res, ctx) => res(ctx.json(response))));

        const mediaItem = await mediaService.getMediaItem(datasetIdentifier, mediaIdentifier);

        expect(mediaItem).toEqual({
            identifier: mediaIdentifier,
            name: 'VID_20210209_160431',
            src: API_URLS.MEDIA_ITEM_SRC(datasetIdentifier, mediaIdentifier),
            thumbnailSrc: API_URLS.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, videoIdentifier),
            uploadTime: '2021-08-05T07:02:38.182000+00:00',
            annotationStatePerTask: [
                {
                    taskId,
                    state: MEDIA_ANNOTATION_STATUS.NONE,
                },
            ],
            metadata: {
                height: 1920,
                width: 1080,
                duration: 95,
                frameStride: 60,
                fps: 60,
                frames: 5700,
            },
            status: 'none',
        });
    });

    describe('active dataset', () => {
        const newDatasetIdentifier = {
            workspaceId: '61039c80bd1cde3821dcfca6',
            projectId: '61039c81bd1cde3821dcfcad',
            datasetId: 'dummy',
            organizationId: 'organization-id',
        };

        it('returns an empty array if the endpoint return 204', async () => {
            const mediaUrl = API_URLS.ACTIVE_MEDIA(newDatasetIdentifier, 20);

            server.use(rest.get(apiRequestUrl(mediaUrl), (_req, res, ctx) => res(ctx.status(204))));

            const { media } = await mediaService.getActiveMedia(newDatasetIdentifier, 20);

            expect(media).toEqual([]);
        });

        it('gets active media items and sorts video frames by framenumber', async () => {
            const mediaUrl = API_URLS.ACTIVE_MEDIA(newDatasetIdentifier, 20);

            server.use(rest.get(apiRequestUrl(mediaUrl), (_req, res, ctx) => res(ctx.json(activeMediaResponse()))));

            const { media } = await mediaService.getActiveMedia(newDatasetIdentifier, 20);

            expect(media).toHaveLength(3);

            const imageIdentifier: ImageIdentifier = {
                type: MEDIA_TYPE.IMAGE as const,
                imageId: '61039cccbd1cde3821dcfcb2',
            };
            const firstVideoFrameIdentifier: VideoFrameIdentifier = {
                type: MEDIA_TYPE.VIDEO_FRAME as const,
                videoId: '6103b96e2360313e324963f2',
                frameNumber: 3360,
            };

            const secondVideoFrameIdentifier: VideoFrameIdentifier = {
                type: MEDIA_TYPE.VIDEO_FRAME as const,
                videoId: '6103b96e2360313e324963f2',
                frameNumber: 3300,
            };

            expect(media).toEqual([
                {
                    identifier: secondVideoFrameIdentifier,
                    name: 'VID_20210209_160431',
                    src: API_URLS.MEDIA_ITEM_SRC(newDatasetIdentifier, secondVideoFrameIdentifier),
                    thumbnailSrc: API_URLS.MEDIA_ITEM_THUMBNAIL(newDatasetIdentifier, secondVideoFrameIdentifier),
                    uploadTime: '2021-07-30T08:33:50.399',
                    annotationStatePerTask: [
                        {
                            taskId,
                            state: MEDIA_ANNOTATION_STATUS.NONE,
                        },
                    ],
                    status: MEDIA_ANNOTATION_STATUS.NONE,
                    metadata: {
                        height: 1920,
                        width: 1080,
                        fps: 60,
                        duration: 95,
                        frames: 5700,
                        frameStride: 60,
                    },
                },
                {
                    identifier: firstVideoFrameIdentifier,
                    name: 'VID_20210209_160431',
                    src: API_URLS.MEDIA_ITEM_SRC(newDatasetIdentifier, firstVideoFrameIdentifier),
                    thumbnailSrc: API_URLS.MEDIA_ITEM_THUMBNAIL(newDatasetIdentifier, firstVideoFrameIdentifier),
                    uploadTime: '2021-07-30T08:33:50.399',
                    annotationStatePerTask: [
                        {
                            taskId,
                            state: MEDIA_ANNOTATION_STATUS.NONE,
                        },
                    ],
                    status: MEDIA_ANNOTATION_STATUS.NONE,
                    metadata: {
                        height: 1920,
                        width: 1080,
                        fps: 60,
                        duration: 95,
                        frames: 5700,
                        frameStride: 60,
                    },
                },
                {
                    identifier: imageIdentifier,
                    name: 'IMG_20201020_111432',
                    src: API_URLS.MEDIA_ITEM_SRC(newDatasetIdentifier, imageIdentifier),
                    thumbnailSrc: API_URLS.MEDIA_ITEM_THUMBNAIL(newDatasetIdentifier, imageIdentifier),
                    uploadTime: '2021-07-30T08:33:50.399',
                    annotationStatePerTask: [
                        {
                            taskId,
                            state: MEDIA_ANNOTATION_STATUS.NONE,
                        },
                    ],
                    status: MEDIA_ANNOTATION_STATUS.NONE,
                    metadata: {
                        height: 1599,
                        width: 899,
                    },
                },
            ]);
        });
    });
});
