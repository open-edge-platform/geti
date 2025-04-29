// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';

import { MEDIA_TYPE } from '../../media/base-media.interface';
import { Image } from '../../media/image.interface';
import { TASK_TYPE } from '../../projects/dtos/task.interface';
import { JobInfoStatus } from '../dtos/tests.interface';
import { TestImageMediaItem } from '../test-image.interface';
import { MetricType, Test, TestScore } from '../tests.interface';

const mockedTest: Test = {
    id: 'test-id',
    testName: 'test-name',
    scores: [
        {
            name: 'score-name-overall',
            labelId: null,
            value: 0.7,
        },
        {
            name: 'score-name',
            labelId: 'label-id',
            value: 0.7,
        },
    ],
    averagedScore: 0.7,
    jobInfo: {
        id: 'job-info-id',
        status: JobInfoStatus.DONE,
    },
    modelInfo: {
        id: 'model-id',
        version: 1,
        numberOfLabels: 2,
        modelTemplateName: 'Speed',
        groupId: 'architecture-id',
        groupName: 'ATSS',
        modelTemplateId: 'template-id',
        taskType: TASK_TYPE.DETECTION,
        optimizationType: 'Post training optimization',
        creationDate: dayjs().toString(),
        precision: 'FP32',
    },
    creationTime: dayjs().toString(),
    datasetsInfo: [
        {
            id: 'dataset-id',
            datasetName: 'dataset-name',
            isDeleted: false,
            numberOfFrames: 2,
            numberOfImages: 4,
            numberOfSamples: 1,
        },
    ],
    scoreDescription: MetricType.IMAGE_SCORE,
};

export const getMockedTest = (test?: Partial<Test>): Test => ({
    ...mockedTest,
    ...test,
});

const defaultImage: Image = {
    identifier: {
        type: MEDIA_TYPE.IMAGE,
        imageId: 'image-id',
    },
    thumbnailSrc: 'url',
    src: 'url',
    name: 'image-name',
    metadata: {
        width: 100,
        height: 100,
        size: 1234,
    },
    annotationStatePerTask: [],
    uploadTime: dayjs().toString(),
    uploaderId: 'user-id',
    lastAnnotatorId: null,
};
export const getMockedTestImageMediaItem = (
    media?: Partial<TestImageMediaItem>,
    scores?: TestScore[]
): TestImageMediaItem => {
    return {
        type: MEDIA_TYPE.IMAGE,
        media: defaultImage,
        testResult: {
            annotationId: 'annotation-id',
            predictionId: 'prediction-id',
            scores: scores ?? [
                {
                    name: 'score-name-overall',
                    labelId: null,
                    value: 0.7,
                },
                {
                    name: 'score-name',
                    labelId: 'label-id',
                    value: 0.7,
                },
            ],
        },
        ...media,
    };
};
