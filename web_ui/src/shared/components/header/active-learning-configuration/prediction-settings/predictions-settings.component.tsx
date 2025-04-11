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

import { FC } from 'react';

import { Content, ContextualHelp, Flex, Heading, Radio, RadioGroup, Text, View } from '@adobe/react-spectrum';

import { InferenceModel } from '../../../../../core/annotations/services/visual-prompt-service';
import { AnnotatorSettingsConfig, FEATURES_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { useUserProjectSettings } from '../../../../../core/user-settings/hooks/use-project-settings.hook';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { useSelectedInferenceModel } from '../../../../../pages/annotator/providers/selected-media-item-provider/use-selected-inference-model';
import { useCanSelectDifferentInferenceModel } from '../../../../../pages/annotator/tools/explanation-tool/select-model.component';
import { Switch } from '../../../switch/switch.component';

const ToggleSuggestPredictions = () => {
    const projectIdentifier = useProjectIdentifier();
    const settings = useUserProjectSettings(projectIdentifier);
    const config = settings.config as AnnotatorSettingsConfig;
    const suggestPredictions = config[FEATURES_KEYS.INITIAL_PREDICTION].isEnabled;

    const onChange = (isEnabled: boolean) => {
        settings.saveConfig({
            ...settings.config,
            [FEATURES_KEYS.INITIAL_PREDICTION]: { ...config[FEATURES_KEYS.INITIAL_PREDICTION], isEnabled },
        });
    };

    return (
        <Flex alignItems='center' gap={'size-100'}>
            <Switch
                isEmphasized
                id={'suggest-predictions'}
                margin={0}
                justifySelf={'end'}
                gridArea={'autoTrainingSwitch'}
                aria-label={`Suggest predictions`}
                isSelected={suggestPredictions}
                isDisabled={settings.isSavingConfig}
                onChange={onChange}
                UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-800)' }}
            />
            <label htmlFor='suggest-predictions'>
                <Text>Suggest predictions</Text>
            </label>
        </Flex>
    );
};

const ModelTypeContextualHelp = () => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>
                    Select the model that will generate the predictions on your data to get insight into the model
                    performance and to accelerate data annotation. You can choose between the default active learning
                    model or the prompt model.
                </Text>
            </Content>
        </ContextualHelp>
    );
};

const ModelType: FC = () => {
    const [selectedModelType, setSelectedModelType] = useSelectedInferenceModel();

    const handleChangeModelType = (value: string) => {
        setSelectedModelType(value as InferenceModel);
    };

    return (
        <RadioGroup
            label={'Model type'}
            isEmphasized
            value={selectedModelType}
            onChange={handleChangeModelType}
            width={'100%'}
            contextualHelp={<ModelTypeContextualHelp />}
            marginTop={'size-50'}
        >
            <Flex alignItems={'center'} gap={'size-100'}>
                <Radio value={InferenceModel.ACTIVE_MODEL}>Active learning model</Radio>
                <Radio value={InferenceModel.VISUAL_PROMPT}>Prompt model</Radio>
            </Flex>
        </RadioGroup>
    );
};

export const PredictionsSettings = () => {
    const canSelectDifferentInferenceModel = useCanSelectDifferentInferenceModel();

    return (
        <View>
            <Heading level={3} marginY={0} marginBottom={'size-200'}>
                Predictions
            </Heading>

            <ToggleSuggestPredictions />

            {canSelectDifferentInferenceModel && <ModelType />}
        </View>
    );
};
