// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VideoFrame } from '../../media/video.interface';

export interface TrainingDatasetRevision {
    id: string;
    trainingSubset: number;
    testingSubset: number;
    validationSubset: number;
}

export interface TrainingDatasetInfo {
    revisionId: string;
    storageId: string;
}

export interface TrainingDatasetRevisionVideo {
    frames: VideoFrame[];
    matchedFrames: number;
}
