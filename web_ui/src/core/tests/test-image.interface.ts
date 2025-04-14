// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_TYPE } from '../media/base-media.interface';
import { Image } from '../media/image.interface';
import { TestScore } from './tests.interface';

export interface TestImageMediaResult {
    annotationId: string;
    predictionId: string;
    scores: TestScore[];
}

export interface TestImageMediaItem {
    type: MEDIA_TYPE.IMAGE;
    media: Image;
    testResult: TestImageMediaResult;
}
