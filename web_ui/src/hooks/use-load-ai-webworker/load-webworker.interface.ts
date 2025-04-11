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

import { InferenceImageWorker } from '../../pages/annotator/components/explanation/inference-image.interface';
import { GrabcutWorker } from '../../pages/annotator/tools/grabcut-tool/grabcut-tool.interface';
import { IntelligentScissorsWorker } from '../../pages/annotator/tools/polygon-tool/polygon-tool.interface';
import { RITMWorker } from '../../pages/annotator/tools/ritm-tool/ritm-tool.interface';
import {
    SegmentAnythingDecoderWorker,
    SegmentAnythingEncoderWorker,
} from '../../pages/annotator/tools/segment-anything-tool/segment-anything.interface';
import { SSIMWorker } from '../../pages/annotator/tools/ssim-tool/ssim-tool.interface';
import { WatershedWorker } from '../../pages/annotator/tools/watershed-tool/watershed-tool.interface';
import { AlgorithmType } from './algorithm.interface';

export type GetiWorker =
    | GrabcutWorker
    | WatershedWorker
    | IntelligentScissorsWorker
    | RITMWorker
    | SSIMWorker
    | InferenceImageWorker
    | SegmentAnythingEncoderWorker
    | SegmentAnythingDecoderWorker;

export type MapAlgorithmToWorker = {
    // E.g. [AlgorithmType.GRABCUT]: GrabcutWorker
    [K in AlgorithmType]: Extract<GetiWorker, { type: K }>;
};
