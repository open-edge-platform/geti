// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isNil from 'lodash/isNil';
import { v4 as uuidv4 } from 'uuid';

import { MEDIA_TYPE } from '../../media/base-media.interface';
import { Image } from '../../media/image.interface';
import { getAnnotationStatePerTaskFromDTO } from '../../media/services/utils';
import { ModelsGroups, ModelVersion } from '../../models/models.interface';
import {
    BASELINE_MODEL,
    ONNX_MODEL,
    OPENVINO_BASE_MODEL,
    POT_OPTIMIZATION,
    PYTORCH_MODEL,
} from '../../models/optimized-models.interface';
import { getOptimizationType } from '../../models/services/utils';
import { TestImageMediaResultDTO } from '../dtos/test-image.interface';
import { TestMediaItemDTO } from '../dtos/test-media.interface';
import { JobInfoStatus, RunTestBodyDTO, ScoreMetricDTO, TestDTO, TestScoreDTO } from '../dtos/tests.interface';
import { TestImageMediaResult } from '../test-image.interface';
import { TestMediaItem } from '../test-media.interface';
import { MetricType, Test, TestScore } from '../tests.interface';
import { RunTestBody } from './tests-service.interface';

export const getAverageScore = (scores: TestScore[]): TestScore | undefined => {
    return scores.find(({ labelId }) => isNil(labelId));
};

const getScoreEntity = (scores: TestScoreDTO[]): TestScore[] =>
    scores.map(({ label_id: labelId, name, value }) => {
        // accuracy means global metric (from backend implementation)
        const newName = name.toLocaleLowerCase().includes('accuracy')
            ? MetricType.IMAGE_SCORE
            : MetricType.OBJECT_SCORE;
        const nameWithoutScore = newName.split(' ')[0];

        return { name: nameWithoutScore, value, labelId };
    });

const getTestResultEntity = (testResult: TestImageMediaResultDTO): TestImageMediaResult => {
    const { annotation_id, scores, prediction_id } = testResult;

    return {
        annotationId: annotation_id,
        predictionId: prediction_id,
        scores: getScoreEntity(scores),
    };
};

export const filterOutUnsuccessfulTest = (test: Test): boolean =>
    ![JobInfoStatus.FAILED, JobInfoStatus.ERROR].includes(test.jobInfo.status);

export const OPTIMIZATION_TYPES_MAP = {
    BASE: BASELINE_MODEL,
    MO: OPENVINO_BASE_MODEL,
    POT: POT_OPTIMIZATION,
    ONNX: ONNX_MODEL,
    PYTORCH: PYTORCH_MODEL,
} as const;

export const getTestEntity = (test: TestDTO, modelsGroups: ModelsGroups[]): Test => {
    const { id, name: testName, scores, datasets_info, model_info, creation_time } = test;
    const { n_labels, version, task_type, template_id, group_id, id: modelId, optimization_type } = model_info;

    const modelGroup = modelsGroups.find(({ groupId }) => groupId === group_id);
    const newScores = getScoreEntity(scores);

    // score whose labelId is null means it's averaged value
    const averagedScore = getAverageScore(newScores);

    const optimizationType = getOptimizationType(optimization_type);

    // There is a small change that we fetch tests while a test was recently created,
    // in this case the server hasn't created a job yet so instead we will return a
    // fake jobInfo that has the pending info and a UUID instead
    const jobInfo = {
        id: test?.job_info?.id ?? uuidv4(),
        status: test?.job_info?.status ?? JobInfoStatus.PENDING,
    };

    /** Note: Normally we should always have model found.
     * If there will be some data mismatch,
     * the only impact will be in item preview dialog - creationDate will be undefined
     * */
    const model = modelGroup?.modelVersions.find((modelVersion) => modelVersion.version === version) as ModelVersion;
    const modelCreationDate = model?.creationDate;
    const [precision] = test.model_info?.precision ?? [];

    return {
        id,
        testName,
        creationTime: creation_time,
        jobInfo,
        modelInfo: {
            version,
            groupId: group_id,
            groupName: modelGroup?.groupName ?? '',
            id: modelId,
            modelTemplateId: template_id,
            modelTemplateName: modelGroup?.modelTemplateName ?? '',
            numberOfLabels: n_labels,
            taskType: task_type,
            optimizationType: OPTIMIZATION_TYPES_MAP[optimizationType],
            creationDate: modelCreationDate,
            precision: precision ?? '',
        },
        datasetsInfo: datasets_info.map(
            ({ id: datasetId, name: datasetName, is_deleted, n_images, n_samples, n_frames }) => ({
                datasetName: datasetName === '' && is_deleted ? 'Deleted dataset' : datasetName,
                id: datasetId,
                isDeleted: is_deleted,
                numberOfFrames: n_frames,
                numberOfImages: n_images,
                numberOfSamples: n_samples,
            })
        ),
        scores: newScores,
        averagedScore: averagedScore?.value ?? 0,
        scoreDescription: averagedScore?.name ?? '',
    };
};

export const getTestMediaItemEntity = (mediaItem: TestMediaItemDTO): TestMediaItem => {
    const { name, annotation_state_per_task, thumbnail, upload_time, uploader_id, id, last_annotator_id } = mediaItem;

    const baseMediaItem = {
        name,
        thumbnailSrc: thumbnail,
        uploadTime: upload_time,
        uploaderId: uploader_id,
        annotationStatePerTask: getAnnotationStatePerTaskFromDTO(annotation_state_per_task),
        lastAnnotatorId: last_annotator_id,
    };

    switch (mediaItem.type) {
        case MEDIA_TYPE.IMAGE: {
            const { height, width, display_url, size } = mediaItem.media_information;

            const imageMedia: Image = {
                ...baseMediaItem,
                identifier: {
                    imageId: id,
                    type: MEDIA_TYPE.IMAGE,
                },
                metadata: {
                    width,
                    height,
                    size,
                },
                src: display_url,
            };

            return {
                type: MEDIA_TYPE.IMAGE,
                media: imageMedia,
                testResult: getTestResultEntity(mediaItem.test_result),
            };
        }
        case MEDIA_TYPE.VIDEO: {
            const {
                height,
                width,
                frame_count: frames,
                frame_stride: frameStride,
                duration,
                display_url,
                size,
            } = mediaItem.media_information;
            const fps = frames / duration;
            const filteredFrames = mediaItem.filtered_frames ? Object.keys(mediaItem.filtered_frames) : [];

            return {
                type: MEDIA_TYPE.VIDEO,
                media: {
                    ...baseMediaItem,
                    identifier: {
                        videoId: id,
                        type: MEDIA_TYPE.VIDEO,
                    },
                    metadata: {
                        size,
                        width,
                        height,
                        duration,
                        fps,
                        frames,
                        frameStride,
                    },
                    src: display_url,
                },
                matchedFrames: mediaItem.matched_frames ?? 0,
                filteredFrames: filteredFrames.map((frameIndex) => {
                    const { prediction_id, scores, annotation_id } = mediaItem.filtered_frames[Number(frameIndex)];

                    return {
                        frameIndex: Number(frameIndex),
                        ...getTestResultEntity({ prediction_id, scores, annotation_id }),
                    };
                }),
            };
        }
        case MEDIA_TYPE.VIDEO_FRAME: {
            const {
                size,
                height,
                width,
                frame_count: frames,
                frame_stride: frameStride,
                duration,
                display_url,
            } = mediaItem.media_information;
            const fps = frames / duration;
            const frameNumber = mediaItem.frame_index;

            return {
                type: MEDIA_TYPE.VIDEO_FRAME,
                media: {
                    ...baseMediaItem,
                    identifier: {
                        type: MEDIA_TYPE.VIDEO_FRAME,
                        videoId: mediaItem.video_id,
                        frameNumber,
                    },
                    metadata: {
                        size,
                        width,
                        height,
                        duration,
                        fps,
                        frames,
                        frameStride,
                    },
                    src: display_url,
                },
                testResult: getTestResultEntity(mediaItem.test_result),
            };
        }
        default: {
            throw new Error(`Unsupported media type`);
        }
    }
};

export const getRunTestBodyDTO = (body: RunTestBody): RunTestBodyDTO => {
    const { name, modelId, modelGroupId, datasetIds, metric } = body;

    const responseDTO = {
        name,
        model_id: modelId,
        model_group_id: modelGroupId,
        dataset_ids: datasetIds,
    };

    return metric
        ? { ...responseDTO, metric: metric === MetricType.IMAGE_SCORE ? ScoreMetricDTO.GLOBAL : ScoreMetricDTO.LOCAL }
        : responseDTO;
};
