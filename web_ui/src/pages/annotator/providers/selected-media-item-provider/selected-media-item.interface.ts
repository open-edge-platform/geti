// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { PredictionResult } from '../../../../core/annotations/services/prediction-service.interface';
import { MediaItem } from '../../../../core/media/media.interface';

export type SelectedMediaItem = MediaItem & {
    image: ImageData;
    annotations: Annotation[];
    predictions?: PredictionResult;
};
