// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isObject } from 'lodash-es';
import { rest } from 'msw';

import { apiRequestUrl } from '../../../../packages/core/src/services/test-utils';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import {
    getMockedImageMediaItem,
    getMockedVideoMediaItem,
} from '../../../test-utils/mocked-items-factory/mocked-media';
import { LABEL_BEHAVIOUR } from '../../labels/label.interface';
import { MEDIA_TYPE } from '../../media/base-media.interface';
import { MediaItem } from '../../media/media.interface';
import { API_URLS } from '../../services/urls';
import { RangeAnnotationDTO } from '../dtos/annotation.interface';
import { ShapeType } from '../shapetype.enum';
import { labelFromUser } from '../utils';
import { createApiAnnotationService } from './api-annotation-service';
import { imageAnnotationsResponse, imageKeypointAnnotationsResponse, videoAnnotationsResponse } from './mockResponses';
import { server } from './test-utils';

const PROJECT_LABELS = [
    getMockedLabel({ id: '60b609e0d036ba4566726c82', name: 'card', color: '#fff5f7ff' }),

    getMockedLabel({
        id: '60b6153817057389ba93f42e',
        name: 'card',
        color: '#3f00ffff',
        group: '',
        parentLabelId: null,
        hotkey: '',
        behaviour: LABEL_BEHAVIOUR.LOCAL,
    }),
];

describe('API annotation service', () => {
    const media: MediaItem = getMockedImageMediaItem({
        identifier: {
            imageId: '60b609fbd036ba4566726c96',
            type: MEDIA_TYPE.IMAGE,
        },
    });

    const datasetIdentifier = {
        workspaceId: 'workspace-id',
        projectId: 'project-id',
        datasetId: 'dataset-id',
        organizationId: 'organization-id',
    };

    it('gets annotations and retrieves their labels', async () => {
        const annotationUrl = API_URLS.ANNOTATIONS(datasetIdentifier, media.identifier);

        server.use(
            rest.get(apiRequestUrl(annotationUrl), (_req, res, ctx) => {
                return res(ctx.json(imageAnnotationsResponse()));
            })
        );

        const annotationService = createApiAnnotationService();
        const annotations = await annotationService.getAnnotations(datasetIdentifier, PROJECT_LABELS, media);

        const expectedLabel = {
            ...labelFromUser(PROJECT_LABELS[1]),
            source: { userId: 'default_user', modelId: undefined, modelStorageId: undefined },
            score: undefined,
        };

        expect(annotations).toHaveLength(4);
        expect(annotations[0]).toEqual({
            id: 'd69b4403-4f4c-4e66-936e-b8565dd1a8a1',
            isHidden: false,
            isSelected: false,
            isLocked: false,
            labels: [expectedLabel],
            shape: { shapeType: ShapeType.Rect, x: 65, y: 31, width: 19, height: 16 },
            zIndex: 0,
        });
        expect(annotations[1]).toEqual({
            id: '54af0335-5074-4024-a9dc-f04417ab1b1c',
            isHidden: false,
            isSelected: false,
            isLocked: false,
            labels: [expectedLabel],
            shape: { shapeType: ShapeType.Circle, x: 34, y: 16, r: 15 },
            zIndex: 1,
        });
        expect(annotations[2]).toEqual({
            id: 'ccfb81c6-a162-4f8f-b1c2-f97f51b0949d',
            isHidden: false,
            isSelected: false,
            isLocked: false,
            labels: [expectedLabel],
            shape: {
                shapeType: ShapeType.Polygon,
                points: [
                    { x: 20, y: 20 },
                    { x: 40, y: 20 },
                    { x: 30, y: 30 },
                ],
            },
            zIndex: 2,
        });
        expect(annotations[3]).toEqual({
            id: '54af0335-5074-4024-a9dc-f04417ab1b1c',
            isHidden: false,
            isSelected: false,
            isLocked: false,
            labels: [expectedLabel],
            shape: { shapeType: ShapeType.Circle, x: 34, y: 21, r: 20 },
            zIndex: 3,
        });
    });

    it('gets single project keypoint annotation', async () => {
        const annotationUrl = API_URLS.ANNOTATIONS(datasetIdentifier, media.identifier);

        server.use(
            rest.get(apiRequestUrl(annotationUrl), (_req, res, ctx) => {
                return res(ctx.json(imageKeypointAnnotationsResponse()));
            })
        );

        const annotationService = createApiAnnotationService();
        const annotations = await annotationService.getAnnotations(datasetIdentifier, PROJECT_LABELS, media);

        expect(annotations).toHaveLength(1);
        expect(annotations[0]).toEqual({
            id: 'test-1',
            isHidden: false,
            isSelected: false,
            isLocked: false,
            labels: [expect.objectContaining({ id: '60b609e0d036ba4566726c82' })],
            shape: {
                shapeType: ShapeType.Pose,
                points: [
                    expect.objectContaining({
                        x: 0,
                        y: 0,
                        label: expect.objectContaining({ id: '60b609e0d036ba4566726c82' }),
                    }),
                    expect.objectContaining({
                        x: 10,
                        y: 10,
                        label: expect.objectContaining({ id: '60b6153817057389ba93f42e' }),
                    }),
                ],
            },
            zIndex: 0,
        });
    });

    it('retrieves video timeline annotations per video frame correctly', async () => {
        const videoMediaItem: MediaItem = getMockedVideoMediaItem({
            identifier: {
                videoId: '60b609fbd036ba4566726c96',
                type: MEDIA_TYPE.VIDEO,
            },
            metadata: {
                height: 100,
                width: 100,
                fps: 30,
                duration: 60,
                frames: 10,
                frameStride: 60,
                size: 1234,
            },
        });
        const annotationUrl = API_URLS.ANNOTATIONS(datasetIdentifier, videoMediaItem.identifier);

        server.use(
            rest.get(apiRequestUrl(annotationUrl), (_req, res, ctx) => {
                return res(ctx.json(videoAnnotationsResponse()));
            })
        );

        const annotationService = createApiAnnotationService();
        const annotations = await annotationService.getVideoAnnotations(
            datasetIdentifier,
            PROJECT_LABELS,
            videoMediaItem
        );

        expect(annotations[1]).toHaveLength(4);
        expect(Object.keys(annotations)).toHaveLength(1);
    });

    it('returns annotations correctly if the video annotation properties are wrong', async () => {
        const videoMediaItem: MediaItem = getMockedVideoMediaItem({
            identifier: {
                videoId: '60b609fbd036ba4566726c96',
                type: MEDIA_TYPE.VIDEO,
            },
            metadata: {
                height: 100,
                width: 100,
                fps: 30,
                duration: 60,
                frames: 10,
                frameStride: 60,
                size: 3214,
            },
        });
        const annotationUrl = API_URLS.ANNOTATIONS(datasetIdentifier, videoMediaItem.identifier);

        server.use(
            rest.get(apiRequestUrl(annotationUrl), (_req, res, ctx) => {
                const response = videoAnnotationsResponse();

                return res(
                    ctx.json({
                        ...response,
                        video_annotation_properties: {
                            end_frame: 100,
                            requested_end_frame: Infinity,
                            requested_start_frame: 0,
                            start_frame: 0,
                            total_count: -1,
                            total_requested_count: Infinity,
                        },
                    })
                );
            })
        );

        const annotationService = createApiAnnotationService();
        const annotations = await annotationService.getVideoAnnotations(
            datasetIdentifier,
            PROJECT_LABELS,
            videoMediaItem
        );

        // We only care about checking that we received some annotations
        expect(Object.keys(annotations)).toHaveLength(1);
    });

    it('returns an empty list in case of a 404 response', async () => {
        const annotationUrl = API_URLS.ANNOTATIONS(datasetIdentifier, media.identifier);

        server.use(
            rest.get(apiRequestUrl(annotationUrl), (_req, res, ctx) => {
                return res(
                    ctx.status(404),
                    ctx.json({
                        error_code: 'prediction_not_found',
                        http_status: 404,
                        message: 'There are no annotations that belong to the given image',
                    })
                );
            })
        );

        const annotationService = createApiAnnotationService();
        const annotations = await annotationService.getAnnotations(datasetIdentifier, PROJECT_LABELS, media);

        expect(annotations).toHaveLength(0);
    });

    it('normalizes annotations before saving them', async () => {
        const annotationUrl = API_URLS.SAVE_ANNOTATIONS(datasetIdentifier, media.identifier);

        server.use(
            rest.post(annotationUrl, (_req, res, ctx) => {
                return res(ctx.json({ message: 'ok' }));
            })
        );

        const annotationService = createApiAnnotationService();

        const label = {
            ...labelFromUser(
                getMockedLabel({
                    id: '60b6153817057389ba93f42e',
                    name: 'card',
                    color: '#3f00ffff',
                    group: '',
                    parentLabelId: null,
                    hotkey: '',

                    behaviour: LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL,
                })
            ),
            score: 1.0,
        };
        const annotations = [
            {
                id: 'd69b4403-4f4c-4e66-936e-b8565dd1a8a1',
                isHidden: false,
                isSelected: false,
                isLocked: false,
                labels: [label],
                shape: { shapeType: ShapeType.Rect as const, x: 65, y: 31, width: 19, height: 16 },
                zIndex: 0,
            },
            {
                id: '54af0335-5074-4024-a9dc-f04417ab1b1c',
                isHidden: false,
                isSelected: false,
                isLocked: false,
                labels: [label],
                shape: { shapeType: ShapeType.Circle as const, x: 34.5, y: 18.5, r: 15.5 },
                zIndex: 1,
            },
            {
                id: 'ccfb81c6-a162-4f8f-b1c2-f97f51b0949d',
                isHidden: false,
                isSelected: false,
                isLocked: false,
                labels: [label],
                shape: {
                    shapeType: ShapeType.Polygon as const,
                    points: [
                        { x: 20, y: 20 },
                        { x: 40, y: 20 },
                        { x: 30, y: 30 },
                    ],
                },
                zIndex: 2,
            },
        ];

        await annotationService.saveAnnotations(datasetIdentifier, media, annotations);
    });

    it('retrieves labeled video ranges', async () => {
        const labels = [
            getMockedLabel({ id: 'normal', name: 'Normal', color: 'var(--brand-moss)' }),
            getMockedLabel({ id: 'anomalous', name: 'Anomalous', color: 'var(--brand-coral-cobalt)' }),
        ];

        const videoMediaItem: MediaItem = getMockedVideoMediaItem({
            identifier: {
                videoId: '60b609fbd036ba4566726c96',
                type: MEDIA_TYPE.VIDEO,
            },
            metadata: {
                height: 100,
                width: 100,
                fps: 30,
                duration: 60,
                frames: 150,
                frameStride: 30,
                size: 691234,
            },
        });
        const annotationUrl = API_URLS.RANGE_ANNOTATIONS(datasetIdentifier, videoMediaItem.identifier);

        server.use(
            rest.get(apiRequestUrl(annotationUrl), (_req, res, ctx) => {
                return res(
                    ctx.json({
                        range_labels: [
                            {
                                start_frame: 0,
                                end_frame: 60 + videoMediaItem.metadata.frameStride - 1,
                                label_ids: [labels[0].id],
                            },
                            {
                                start_frame: 90,
                                end_frame: 149,
                                label_ids: [labels[1].id],
                            },
                        ],
                        videoId: 'video-id',
                        id: 'id',
                    })
                );
            })
        );

        const annotationService = createApiAnnotationService();
        const ranges = await annotationService.getLabeledVideoRanges(datasetIdentifier, videoMediaItem, labels);

        expect(ranges).toEqual([
            { start: 0, end: 60 + videoMediaItem.metadata.frameStride - 1, labels: [labels[0]] },
            { start: 90, end: 149, labels: [labels[1]] },
        ]);
    });

    it('saves labeled video ranges', async () => {
        const labels = [
            getMockedLabel({ id: 'normal', name: 'Normal', color: 'var(--brand-moss)' }),
            getMockedLabel({ id: 'anomalous', name: 'Anomalous', color: 'var(--brand-coral-cobalt)' }),
        ];

        const videoMediaItem: MediaItem = getMockedVideoMediaItem({
            identifier: {
                videoId: '60b609fbd036ba4566726c96',
                type: MEDIA_TYPE.VIDEO,
            },
            metadata: {
                height: 100,
                width: 100,
                fps: 30,
                duration: 60,
                frames: 151,
                frameStride: 30,
                size: 123469,
            },
        });

        const rangeAnnotationUrl = API_URLS.RANGE_ANNOTATIONS(datasetIdentifier, videoMediaItem.identifier);

        const saveRanges = jest.fn();

        server.use(
            rest.post(rangeAnnotationUrl, async (req, res, ctx) => {
                const body = await req.json<RangeAnnotationDTO>();
                if (isObject(body)) {
                    saveRanges(body['range_labels']);
                }

                return res(ctx.json({ message: 'ok' }));
            })
        );

        const annotationService = createApiAnnotationService();

        // The following fails if we did not mock all endpoints that are called by the service
        await annotationService.saveLabeledVideoRanges(datasetIdentifier, videoMediaItem, [
            { start: 0, end: 60 + videoMediaItem.metadata.frameStride - 1, labels: [labels[0]] },
            { start: 90, end: 151, labels: [labels[1]] },
        ]);

        expect(saveRanges).toHaveBeenCalledWith([
            { start_frame: 0, end_frame: 89, label_ids: [labels[0].id] },
            { start_frame: 90, end_frame: 151, label_ids: [labels[1].id] },
        ]);
    });
});
