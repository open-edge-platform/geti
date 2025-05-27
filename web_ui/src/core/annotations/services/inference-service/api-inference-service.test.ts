// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { partial } from 'lodash-es';
import { rest } from 'msw';

import { apiRequestUrl } from '../../../../../packages/core/src/services/test-utils';
import { API_URLS } from '../../../../../packages/core/src/services/urls';
import { loadImageFromFile } from '../../../../shared/media-utils';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import {
    getMockedImageMediaItem,
    getMockedVideoMediaItem,
} from '../../../../test-utils/mocked-items-factory/mocked-media';
import { LABEL_BEHAVIOUR } from '../../../labels/label.interface';
import { MEDIA_TYPE } from '../../../media/base-media.interface';
import { TaskChainInput } from '../../annotation.interface';
import { Rect } from '../../shapes.interface';
import { ShapeType } from '../../shapetype.enum';
import {
    getBatchPredictionsResponse,
    mockedExplanation,
    mockedInferencePolygonPrediction,
    mockedInferencePrediction,
    mockedKeypointInferencePrediction,
} from '../mockResponses';
import { PredictionCache, PredictionMode } from '../prediction-service.interface';
import { server } from '../test-utils';
import { getPredictionCache } from '../utils';
import { createApiInferenceService } from './api-inference-service';
import { convertBatchToRecord } from './utils';

jest.mock('../../../../shared/media-utils', () => ({
    ...jest.requireActual('../../../../shared/media-utils'),
    loadImageFromFile: jest.fn(),
}));

jest.mock('./utils', () => ({
    ...jest.requireActual('./utils'),
    convertBatchToRecord: jest.fn(),
}));

const labelOne = getMockedLabel({
    id: '60b609e0d036ba4566726c82',
    name: 'card_1',
    color: '#fff5f7ff',
});
const labelTwo = getMockedLabel({
    id: '60b6153817057389ba93f42e',
    name: 'card_2',
    color: '#3f00ffff',
    group: '',
    hotkey: '',
    behaviour: LABEL_BEHAVIOUR.LOCAL,
});

const emptyLabel = getMockedLabel({
    id: '656f2ea24812a949d5cffeca',
    name: 'Empty',
    isEmpty: true,
});

const PROJECT_LABELS = [labelOne, labelTwo, emptyLabel];

describe('API inference service', () => {
    const videoMediaItem = getMockedVideoMediaItem({});
    const mockedImageMedia = getMockedImageMediaItem({
        identifier: { imageId: '60b609fbd036ba4566726c96', type: MEDIA_TYPE.IMAGE },
    });

    const taskId = '12321';
    const probability = 0.2;
    const userId = 'user-email@test.com';
    const roiShape = { x: 10, y: 10, width: 50, height: 50 };
    const datasetIdentifier = {
        workspaceId: 'workspace-id',
        projectId: 'project-id',
        datasetId: 'dataset-id',
        organizationId: 'organization-id',
    };

    const inferenceService = createApiInferenceService();
    const selectedInputLabelTwo = getMockedAnnotation({
        id: 'test-annotation-2',
        isSelected: true,
        shape: { shapeType: ShapeType.Rect, ...roiShape },
        labels: [{ ...labelTwo, source: { userId } }],
    }) as TaskChainInput;

    describe('getPredictions', () => {
        const predictionResponse = mockedInferencePrediction({ ...labelOne, probability });
        const { type: deleteType, ...shapeResponse } = predictionResponse.shape;

        const inference = API_URLS.PREDICTION_NEW(datasetIdentifier, PredictionCache.AUTO);
        const inferenceTaskUrl = API_URLS.PREDICTION_NEW(datasetIdentifier, PredictionCache.AUTO, taskId);
        const getImageAutoPredictions = partial(
            inferenceService.getPredictions,
            datasetIdentifier,
            PROJECT_LABELS,
            mockedImageMedia,
            PredictionCache.AUTO
        );

        it('video is rejected', async () => {
            server.use(rest.post(apiRequestUrl(inference), (_req, res, ctx) => res(ctx.json(null))));

            return expect(
                inferenceService.getPredictions(datasetIdentifier, PROJECT_LABELS, videoMediaItem, PredictionCache.AUTO)
            ).rejects.toThrow('video is not supported');
        });

        it('empty data', async () => {
            server.use(rest.post(apiRequestUrl(inference), (_req, res, ctx) => res(ctx.json(null))));

            const response = await getImageAutoPredictions();

            expect(response).toEqual([]);
        });

        it('calls active:predict', async () => {
            server.use(
                rest.post(apiRequestUrl(inference), (_req, res, ctx) =>
                    res(
                        ctx.json({
                            created: '2021-06-03T13:09:18.096000+00:00',
                            predictions: [predictionResponse],
                        })
                    )
                )
            );

            const response = await getImageAutoPredictions();

            expect(response).toEqual([
                {
                    id: expect.any(String),
                    isHidden: false,
                    isSelected: false,
                    isLocked: false,
                    labels: [
                        {
                            ...labelOne,
                            score: probability,
                            source: {
                                modelId: 'latest',
                                modelStorageId: 'storage_id',
                            },
                        },
                    ],
                    shape: { ...shapeResponse, shapeType: 1 },
                    zIndex: 0,
                },
            ]);
        });

        it('calls taskId:predict with roi config, selectedInput labels are added to the new prediction', async () => {
            const annotationLabel = { ...labelTwo, source: { userId } };

            const selectedInput = getMockedAnnotation({
                id: 'test-annotation-2',
                isSelected: true,
                shape: { shapeType: ShapeType.Rect, ...roiShape },
                labels: [annotationLabel],
            }) as TaskChainInput;

            server.use(
                rest.post(apiRequestUrl(inferenceTaskUrl), (_req, res, ctx) =>
                    res(ctx.json({ created: '2021-06-03T13:09:18.096000+00:00', predictions: [predictionResponse] }))
                )
            );

            const response = await getImageAutoPredictions(taskId, selectedInput);

            expect(response).toEqual([
                {
                    id: expect.any(String),
                    isHidden: false,
                    isSelected: false,
                    isLocked: false,
                    labels: [
                        {
                            ...labelOne,
                            score: probability,
                            source: {
                                modelId: 'latest',
                                modelStorageId: 'storage_id',
                                userId: undefined,
                            },
                        },
                        {
                            ...annotationLabel,
                        },
                    ],
                    shape: { shapeType: 1, ...roiShape },
                    zIndex: 0,
                },
            ]);
        });

        it('does not apply roi config for Polygon predictions', async () => {
            const polygonResponseOne = mockedInferencePolygonPrediction({
                ...labelOne,
                probability,
                points: [{ x: 1, y: 2 }],
            });

            const polygonResponseTwo = mockedInferencePolygonPrediction({
                ...labelOne,
                probability,
                points: [{ x: 3, y: 4 }],
            });

            server.use(
                rest.post(apiRequestUrl(inferenceTaskUrl), (_req, res, ctx) =>
                    res(
                        ctx.json({
                            created: '2021-06-03T13:09:18.096000+00:00',
                            predictions: [polygonResponseOne, polygonResponseTwo],
                        })
                    )
                )
            );

            const response = await getImageAutoPredictions(taskId, selectedInputLabelTwo);

            expect(response).toEqual([
                {
                    ...selectedInputLabelTwo,
                    isHidden: false,
                    isLocked: false,
                    isSelected: false,
                    labels: [
                        {
                            ...labelTwo,
                            source: { modelId: undefined, modelStorageId: undefined, userId: 'user-email@test.com' },
                        },
                    ],
                },
                {
                    id: expect.any(String),
                    isHidden: false,
                    isLocked: false,
                    isSelected: false,
                    labels: [
                        {
                            ...labelOne,
                            score: probability,
                            source: { modelId: 'latest', modelStorageId: 'storage_id', userId: undefined },
                        },
                    ],
                    shape: {
                        points: [
                            {
                                x: polygonResponseOne.shape.points[0].x,
                                y: polygonResponseOne.shape.points[0].y,
                            },
                        ],
                        shapeType: 3,
                    },
                    zIndex: 1,
                },
                {
                    id: expect.any(String),
                    isHidden: false,
                    isLocked: false,
                    isSelected: false,
                    labels: [
                        {
                            ...labelOne,
                            score: probability,
                            source: { modelId: 'latest', modelStorageId: 'storage_id', userId: undefined },
                        },
                    ],
                    shape: {
                        points: [
                            {
                                x: polygonResponseTwo.shape.points[0].x,
                                y: polygonResponseTwo.shape.points[0].y,
                            },
                        ],
                        shapeType: 3,
                    },
                    zIndex: 2,
                },
            ]);
        });

        it('returns an empty polygon annotation', async () => {
            const inputRect = selectedInputLabelTwo.shape as Rect;
            const emptyLabelResponse = {
                labels: [
                    {
                        id: emptyLabel.id,
                        name: emptyLabel.name,
                        probability: 0,
                    },
                ],
                shape: {
                    points: null,
                    type: 'POLYGON',
                },
            };

            server.use(
                rest.post(apiRequestUrl(inferenceTaskUrl), (_req, res, ctx) =>
                    res(
                        ctx.json({
                            predictions: [emptyLabelResponse],
                            created: '2023-12-05 14:56:04.207732874 +0000',
                        })
                    )
                )
            );

            const response = await getImageAutoPredictions(taskId, selectedInputLabelTwo);

            expect(response).toEqual([
                {
                    id: selectedInputLabelTwo.id,
                    isHidden: false,
                    isLocked: false,
                    isSelected: false,
                    labels: [
                        {
                            ...labelTwo,
                            score: undefined,
                            source: {
                                modelId: undefined,
                                modelStorageId: undefined,
                                userId: 'user-email@test.com',
                            },
                        },
                        {
                            ...emptyLabel,
                            score: 0,
                            source: {
                                modelId: 'latest',
                                modelStorageId: 'storage_id',
                                userId: undefined,
                            },
                        },
                    ],
                    shape: inputRect,
                    zIndex: 0,
                },
            ]);
        });

        it('return and format keypoint detection predictions', async () => {
            const keypointPredictionResponse = mockedKeypointInferencePrediction({
                probability: 1,
                labels: [labelOne, labelTwo],
            });

            server.use(
                rest.post(apiRequestUrl(inferenceTaskUrl), (_req, res, ctx) =>
                    res(
                        ctx.json({
                            created: '2021-06-03T13:09:18.096000+00:00',
                            predictions: keypointPredictionResponse,
                            media_identifier: { image_id: '67a515e89a4f0d5e2ef03027', type: 'image' },
                        })
                    )
                )
            );

            const response = await getImageAutoPredictions(taskId);

            expect(response).toEqual([
                expect.objectContaining({
                    shape: {
                        shapeType: ShapeType.Pose,
                        points: [
                            expect.objectContaining({
                                label: {
                                    ...labelOne,
                                    score: 1,
                                    source: {
                                        modelId: 'latest',
                                        modelStorageId: 'storage_id',
                                        userId: undefined,
                                    },
                                },
                                x: 1,
                                y: 2,
                            }),
                            expect.objectContaining({
                                label: {
                                    ...labelTwo,
                                    score: 1,
                                    source: {
                                        modelId: 'latest',
                                        modelStorageId: 'storage_id',
                                        userId: undefined,
                                    },
                                },
                                x: 2,
                                y: 3,
                            }),
                        ],
                    },
                }),
            ]);
        });
    });

    describe('getExplanations', () => {
        const explanationResponse = mockedExplanation({ labelId: labelOne.id, labelName: labelTwo.name });
        const [firstMap] = explanationResponse.maps;

        const explanationUrl = API_URLS.EXPLAIN_NEW(datasetIdentifier);
        const explanationTaskUrl = API_URLS.EXPLAIN_NEW(datasetIdentifier, taskId);

        it('video is rejected', () => {
            return expect(inferenceService.getExplanations(datasetIdentifier, videoMediaItem)).rejects.toThrow(
                'video is not supported'
            );
        });

        it('empty data', async () => {
            server.use(rest.post(apiRequestUrl(explanationUrl), (_req, res, ctx) => res(ctx.json(null))));

            const response = await inferenceService.getExplanations(datasetIdentifier, mockedImageMedia);

            expect(response).toEqual([]);
        });

        it('taskId: empty input', async () => {
            server.use(
                rest.post(apiRequestUrl(explanationTaskUrl), (_req, res, ctx) => res(ctx.json(explanationResponse)))
            );

            const response = await inferenceService.getExplanations(datasetIdentifier, mockedImageMedia, taskId);

            expect(response).toEqual([
                {
                    id: expect.any(String),
                    url: '',
                    name: firstMap.label_name,
                    binary: firstMap.data,
                    labelsId: firstMap.label_id,
                    roi: {
                        id: expect.any(String),
                        shape: {
                            x: 0,
                            y: 0,
                            type: '1',
                            width: mockedImageMedia.metadata.width,
                            height: mockedImageMedia.metadata.height,
                        },
                    },
                },
            ]);
        });

        it('taskId: selected input (roi)', async () => {
            server.use(
                rest.post(apiRequestUrl(explanationTaskUrl), (_req, res, ctx) => res(ctx.json(explanationResponse)))
            );

            const response = await inferenceService.getExplanations(
                datasetIdentifier,
                mockedImageMedia,
                taskId,
                selectedInputLabelTwo
            );

            expect(response).toEqual([
                {
                    id: expect.any(String),
                    url: '',
                    name: firstMap.label_name,
                    binary: firstMap.data,
                    labelsId: firstMap.label_id,
                    roi: {
                        id: expect.any(String),
                        shape: { type: '1', ...roiShape },
                    },
                },
            ]);
        });
    });

    describe('getVideoPredictions', () => {
        const mode = PredictionMode.AUTO;
        const mockedBatchResponse = getBatchPredictionsResponse();
        const batchUrl = API_URLS.BATCH_PREDICT(datasetIdentifier, getPredictionCache(mode));
        const frameOptions = { startFrame: 0, endFrame: 12, frameSkip: 2, labelsOnly: false };

        it('empty data', async () => {
            server.use(rest.post(apiRequestUrl(batchUrl), (_req, res, ctx) => res(ctx.json(null))));

            await inferenceService.getVideoPredictions(
                datasetIdentifier,
                PROJECT_LABELS,
                mockedImageMedia,
                mode,
                frameOptions
            );

            expect(convertBatchToRecord).toHaveBeenCalledWith([], PROJECT_LABELS);
        });

        it('formats response using "convertBatchToRecord"', async () => {
            server.use(rest.post(apiRequestUrl(batchUrl), (_req, res, ctx) => res(ctx.json(mockedBatchResponse))));

            await inferenceService.getVideoPredictions(
                datasetIdentifier,
                PROJECT_LABELS,
                mockedImageMedia,
                mode,
                frameOptions
            );

            expect(convertBatchToRecord).toHaveBeenCalledWith(mockedBatchResponse.batch_predictions, PROJECT_LABELS);
        });
    });

    describe('getExplanationsForFile', () => {
        const explanationResponse = mockedExplanation({ labelId: labelOne.id, labelName: labelTwo.name });
        const [firstMap] = explanationResponse.maps;

        const explanationUrl = API_URLS.EXPLAIN_NEW(datasetIdentifier);

        it('empty data', async () => {
            server.use(rest.post(apiRequestUrl(explanationUrl), (_req, res, ctx) => res(ctx.json(null))));
            const mockedFile = new File([], 'name');
            const response = await inferenceService.getExplanationsForFile(datasetIdentifier, mockedFile);

            expect(response).toEqual([]);
        });

        it('use file metadata as roi', async () => {
            const mockedImage = { width: 10, height: 20 } as HTMLImageElement;
            jest.mocked(loadImageFromFile).mockResolvedValue(mockedImage);
            server.use(
                rest.post(apiRequestUrl(explanationUrl), (_req, res, ctx) => res(ctx.json(explanationResponse)))
            );
            const mockedFile = new File([], 'name');
            const response = await inferenceService.getExplanationsForFile(datasetIdentifier, mockedFile);

            expect(response).toEqual([
                {
                    id: expect.any(String),
                    name: firstMap.label_name,
                    binary: firstMap.data,
                    labelsId: firstMap.label_id,
                    roi: {
                        id: expect.any(String),
                        shape: {
                            x: 0,
                            y: 0,
                            type: '1',
                            height: mockedImage.height,
                            width: mockedImage.width,
                        },
                    },
                    url: '',
                },
            ]);
        });
    });
});
