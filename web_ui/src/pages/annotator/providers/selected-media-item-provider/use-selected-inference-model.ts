// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key } from 'react';

import { InferenceModel } from '../../../../core/annotations/services/visual-prompt-service';
import { AnnotatorSettingsConfig, FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useUserProjectSettings } from '../../../../core/user-settings/hooks/use-project-settings.hook';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';

interface UseSelectedInferenceModel {
    (): [InferenceModel, (model: InferenceModel) => void];
}

export const useSelectedInferenceModel: UseSelectedInferenceModel = () => {
    const projectIdentifier = useProjectIdentifier();
    const settings = useUserProjectSettings(projectIdentifier);
    const config = settings.config as AnnotatorSettingsConfig;
    const useActiveModelAsInferenceModel = config[FEATURES_KEYS.INFERENCE_MODEL]?.isEnabled;

    const setSelectedModel = (model: Key) => {
        settings.saveConfig({
            ...settings.config,
            [FEATURES_KEYS.INFERENCE_MODEL]: {
                ...config[FEATURES_KEYS.INFERENCE_MODEL],
                isEnabled: model === InferenceModel.ACTIVE_MODEL,
            },
        });
    };
    const selectedModel = useActiveModelAsInferenceModel ? InferenceModel.ACTIVE_MODEL : InferenceModel.VISUAL_PROMPT;

    return [selectedModel, setSelectedModel];
};
