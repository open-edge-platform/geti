// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { Flex, Item, Picker, Text } from '@geti/ui';

import { InferenceModel } from '../../../../core/annotations/services/visual-prompt-service';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { hasActiveModels } from '../../../../core/models/utils';
import { isAnomalyDomain, isClassificationDomain } from '../../../../core/projects/domains';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useSelectedInferenceModel } from '../../providers/selected-media-item-provider/use-selected-inference-model';

export const useCanSelectDifferentInferenceModel = () => {
    const { FEATURE_FLAG_VISUAL_PROMPT_SERVICE } = useFeatureFlags();
    const { isTaskChainProject, isSingleDomainProject } = useProject();
    const isClassification = isSingleDomainProject(isClassificationDomain) || isSingleDomainProject(isAnomalyDomain);

    if (isClassification || isTaskChainProject || FEATURE_FLAG_VISUAL_PROMPT_SERVICE === false) {
        return false;
    }

    return true;
};

export const SelectInferenceModelPicker = (props: Omit<ComponentProps<typeof Picker>, 'children'>) => {
    const [selectedModel, setSelectedModel] = useSelectedInferenceModel();

    const { useProjectModelsQuery } = useModels();
    const modelsQuery = useProjectModelsQuery();
    const activeModel = modelsQuery.data?.find(hasActiveModels);

    return (
        <Picker
            selectedKey={selectedModel}
            onSelectionChange={(key) =>
                setSelectedModel(key === 'visual_prompt' ? InferenceModel.VISUAL_PROMPT : InferenceModel.ACTIVE_MODEL)
            }
            {...props}
        >
            <Item key='active_model' textValue='Active model'>
                <Text>Active model</Text>
                {activeModel !== undefined && <Text slot='description'>{activeModel.groupName}</Text>}
            </Item>
            <Item key='visual_prompt' textValue='LVM: SAM (Beta)'>
                <Text>LVM: SAM (Beta)</Text>
            </Item>
        </Picker>
    );
};

export const SelectModel = () => {
    const canSelectDifferentInferenceModel = useCanSelectDifferentInferenceModel();

    if (!canSelectDifferentInferenceModel) {
        return null;
    }

    return (
        <Flex gap={{ base: 'size-100', L: 'size-150' }}>
            <SelectInferenceModelPicker label='Model' labelPosition='side' width='size-3000' />

            <Divider size='S' orientation='vertical' />
        </Flex>
    );
};
