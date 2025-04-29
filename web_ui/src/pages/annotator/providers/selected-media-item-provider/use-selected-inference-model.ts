// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
