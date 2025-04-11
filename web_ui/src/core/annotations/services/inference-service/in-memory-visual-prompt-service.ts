// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Label } from '../../../labels/label.interface';
import { MediaItem } from '../../../media/media.interface';
import { DatasetIdentifier } from '../../../projects/dataset.interface';
import { ShapeType } from '../../shapetype.enum';
import { labelFromModel } from '../../utils';
import { InferenceResult } from '../inference-service.interface';
import { VisualPromptService } from '../visual-prompt-service';
import { CreateApiService } from './utils';

export const createInMemoryVisualPromptService: CreateApiService<VisualPromptService> = () => {
    const infer = async (
        _datasetIdentifier: DatasetIdentifier,
        labels: Label[],
        _mediaItem: MediaItem,
        _taskId: string,
        _signal?: AbortSignal
    ): Promise<InferenceResult> => {
        return [
            {
                id: 'rect-1',
                labels: [labelFromModel(labels[1], 0.1, '123', '321'), labelFromModel(labels[0], 0.4, '123', '321')],
                shape: { shapeType: ShapeType.Rect as const, x: 500, y: 100, width: 200, height: 200 },
                zIndex: 0,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
        ];
    };

    return { infer };
};
