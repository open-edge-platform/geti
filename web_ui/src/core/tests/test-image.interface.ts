// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
