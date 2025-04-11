// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key, useEffect, useMemo, useState } from 'react';

import { Flex, Item, Picker, Text } from '@adobe/react-spectrum';
import capitalize from 'lodash/capitalize';
import isEmpty from 'lodash/isEmpty';

import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { PerformanceCategory } from '../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { useSupportedAlgorithms } from '../../../../core/supported-algorithms/hooks/use-supported-algorithms.hook';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { WarningMessage } from '../../../../shared/components/warning-message/warning-message.component';
import { hasEqualId } from '../../../../shared/utils';
import { SelectableOptimizationType } from '../../project-details.interface';
import { getAvailableOptimizationTypes, isModelDeleted, NO_MODELS_MESSAGE } from '../../utils';
import { SelectOptimization } from '../common/select-optimization.component';
import { ModelConfiguration, ModelSelectionProps } from './interfaces';
import { ModelInfo } from './model-info.component';

/*  
    This component is responsible for choosing the architecture, version, and 
    optimization model

    It calculates the optimization models list depending on the user's choice
*/
export const ModelSelection = ({ models, selectedModel, selectModel }: ModelSelectionProps): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { useModelQuery } = useModels();
    const { data: supportedAlgorithms } = useSupportedAlgorithms(projectIdentifier);

    const [localModelConfiguration, setLocalModelConfiguration] = useState<ModelConfiguration>({
        selectedVersionId: selectedModel.versionId || models[0].modelVersions[0].groupId,
        selectedModelGroup: models[0],
        selectedModelVersion: models[0].modelVersions[0],
        selectedOptimizationType: {
            text: '',
            id: models[0].modelVersions[0].id,
        },
    });

    const { selectedModelGroup, selectedVersionId, selectedModelVersion, selectedOptimizationType } =
        localModelConfiguration;

    const { data: modelDetails, isLoading: isLoadingModel } = useModelQuery({
        ...projectIdentifier,
        groupId: selectedModelGroup.groupId,
        modelId: selectedModelVersion.id,
    });

    // Get all optimized models for the selected model. Filter only the ones that finished training and
    // return a formatted object of { id, optimizationType } to be consumed by Options Picker
    const optimizationTypes = useMemo(
        () =>
            modelDetails?.optimizedModels
                .filter((optimizedModel) => optimizedModel.modelStatus === 'SUCCESS')
                .map(({ optimizationType, id, modelName }) => ({ id, optimizationType, modelName })),
        [modelDetails]
    );

    const selectedOptimizedModel = useMemo(() => {
        return modelDetails?.optimizedModels.find(hasEqualId(selectedOptimizationType.id));
    }, [modelDetails?.optimizedModels, selectedOptimizationType.id]);

    const optimizationOptions = useMemo(() => getAvailableOptimizationTypes(optimizationTypes), [optimizationTypes]);

    const handleChangeArchitecture = (key: Key | undefined): void => {
        const newModelGroup = models.find(({ groupId }) => groupId === key);

        if (!newModelGroup) {
            return;
        }

        const newSelectedModelVersion = newModelGroup.modelVersions[0];

        if (!newSelectedModelVersion) {
            return;
        }

        // Update local state with user choices
        setLocalModelConfiguration({
            ...localModelConfiguration,
            selectedModelGroup: newModelGroup,
            selectedModelVersion: newSelectedModelVersion,
            selectedVersionId: newSelectedModelVersion.id,
        });

        // Update the parent's chosen model object
        selectModel({
            modelGroupId: newModelGroup.groupId,
            modelId: newSelectedModelVersion.id,
            optimisationId: selectedOptimizationType.id,
            versionId: newSelectedModelVersion.id,
        });
    };

    const handleChangeModelVersion = (key: Key) => {
        const newSelectedModelVersion = selectedModelGroup.modelVersions.find(hasEqualId(key.toString()));

        if (!newSelectedModelVersion) {
            return;
        }

        setLocalModelConfiguration({
            ...localModelConfiguration,
            selectedModelVersion: newSelectedModelVersion,
            selectedVersionId: key as string,
        });

        selectModel({
            modelGroupId: selectedModelGroup.groupId,
            modelId: newSelectedModelVersion.id,
            optimisationId: selectedOptimizationType.id,
            versionId: key as string,
        });
    };

    const handleSelectOptimizationType = (optimizationType: SelectableOptimizationType): void => {
        setLocalModelConfiguration({
            ...localModelConfiguration,
            selectedOptimizationType: {
                id: optimizationType.id,
                text: optimizationType.text,
            },
        });

        selectModel({
            modelGroupId: selectedModelGroup.groupId,
            versionId: selectedModelVersion.id,
            modelId: optimizationType.id, // "type" is an object containing the new id/name of the trained model
            optimisationId: optimizationType.id,
        });
    };

    // Select the first option by default
    useEffect(() => {
        if (optimizationOptions[0]) {
            handleSelectOptimizationType(optimizationOptions[0]);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [optimizationOptions]);

    if (isEmpty(models)) {
        return <WarningMessage isVisible message={NO_MODELS_MESSAGE} marginTop={'size-250'} />;
    }

    const validModelVersions = selectedModelGroup.modelVersions.filter((model) => !isModelDeleted(model));

    return (
        <Flex direction={'column'} gap={'size-200'}>
            <Flex alignItems={'center'} gap={'size-100'}>
                <Picker
                    label={'Architecture'}
                    items={models}
                    id={'select-architecture-id'}
                    width={'100%'}
                    placeholder={'Select model'}
                    selectedKey={selectedModelVersion?.groupId}
                    onSelectionChange={handleChangeArchitecture}
                >
                    {(item) => {
                        const algorithm = supportedAlgorithms?.find(
                            (algo) => algo.modelTemplateId === item.modelTemplateId
                        );
                        const performanceCategory =
                            algorithm === undefined || algorithm.performanceCategory === PerformanceCategory.OTHER
                                ? ''
                                : capitalize(algorithm.performanceCategory);

                        return (
                            <Item textValue={item.groupName} key={item.groupId}>
                                {`${item.groupName} ${performanceCategory && ` (${performanceCategory})`}`}
                            </Item>
                        );
                    }}
                </Picker>
                <Picker
                    label={'Version'}
                    placeholder={'Select version'}
                    id={'select-version-id'}
                    items={validModelVersions || []}
                    selectedKey={selectedVersionId}
                    onSelectionChange={handleChangeModelVersion}
                    isDisabled={!Boolean(selectedModelVersion)}
                >
                    {(item) => (
                        <Item key={item.id} textValue={`Version ${item.version}`}>
                            <Text id={`version-${item.version}-id`}>Version {item.version}</Text>
                        </Item>
                    )}
                </Picker>
            </Flex>

            {selectedModelVersion && (
                <SelectOptimization
                    options={optimizationOptions}
                    selectedOptimizationType={selectedOptimizationType}
                    setSelectedOptimizationType={handleSelectOptimizationType}
                    isLoading={isLoadingModel}
                />
            )}

            <ModelInfo optimizedModel={selectedOptimizedModel} />
        </Flex>
    );
};
