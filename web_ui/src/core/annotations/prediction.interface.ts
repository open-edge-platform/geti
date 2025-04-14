// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ExplanationDTO } from './dtos/prediction.interface';

export interface Explanation extends Omit<ExplanationDTO, 'label_id'> {
    labelsId: string;
}
