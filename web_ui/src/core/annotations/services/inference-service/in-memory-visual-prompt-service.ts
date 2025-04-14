// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
