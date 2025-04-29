// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
