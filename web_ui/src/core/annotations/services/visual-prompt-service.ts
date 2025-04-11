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
