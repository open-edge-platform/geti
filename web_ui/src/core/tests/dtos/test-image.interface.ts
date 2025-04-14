// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ImageMediaDTO } from '../../media/dtos/image.interface';
import { TestScoreDTO } from './tests.interface';

export interface TestImageMediaResultDTO {
    annotation_id: string;
    prediction_id: string;
    scores: TestScoreDTO[];
}

export interface TestImageMediaItemDTO extends ImageMediaDTO {
    test_result: TestImageMediaResultDTO;
}
