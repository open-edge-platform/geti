// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label } from '../../labels/label.interface';
import { MediaItem } from '../../media/media.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { InferenceResult } from './inference-service.interface';

export enum InferenceModel {
    ACTIVE_MODEL = 'active_model',
    VISUAL_PROMPT = 'visual_prompt',
}

export interface VisualPromptService {
    infer(
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItemId: MediaItem,
        taskId: string,
        abortSignal?: AbortSignal
    ): Promise<InferenceResult>;
}

export const isVisualPromptModelGroup = ({ modelTemplateId }: { modelTemplateId: string }) => {
    return modelTemplateId === 'visual_prompting_model';
};

export const isVisualPromptModel = ({ groupName }: { groupName: string }) => {
    return groupName === 'SAM';
};
