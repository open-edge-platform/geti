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

import { Key, useState } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { useMatch, useNavigate } from 'react-router-dom';

import { isVisualPromptModelGroup } from '../../../../core/annotations/services/visual-prompt-service';
import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { ModelIdentifier, ModelsGroups } from '../../../../core/models/models.interface';
import { paths } from '../../../../core/services/routes';
import { LifecycleStage } from '../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { useSupportedAlgorithms } from '../../../../core/supported-algorithms/hooks/use-supported-algorithms.hook';
import { useModelIdentifier } from '../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
import { Tabs } from '../../../../shared/components/tabs/tabs.component';
import { TabItem } from '../../../../shared/components/tabs/tabs.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { ModelCardMenu } from '../project-models/models-container/model-card/model-card-menu.component';
import { useOptimizedModels } from './hooks/use-optimized-models/use-optimized-models.hook';
import { useSelectedModel } from './hooks/use-selected-model/use-selected-model.hook';
import { ModelBreadcrumb } from './model-breadcrumb/model-breadcrumb.component';
import { ModelConfigurableParameters } from './model-configurable-parameters/model-configurable-parameters.component';
import { ModelLabels } from './model-labels/model-labels.component';
import { ModelStatistics } from './model-statistics/model-statistics.component';
import { ModelVariants } from './model-variants/model-variants.component';
import { PytorchTab } from './model-variants/tabs/pytorch-tab.component';
import { TrainingDataset } from './training-dataset/training-dataset.component';
import { VisualPromptReferenceDataset } from './training-dataset/visual-prompt-reference-dataset.component';
import { getVersionWithDateText } from './utils';
import { VisualPromptModelBetaWarning } from './visual-prompt-model-beta-warning.component';

import classes from './project-model.module.scss';

enum ModelTabsKeys {
    LABELS = 'labels',
    DATASETS = 'training-datasets',
    STATISTICS = 'statistics',
    MODEL_VARIANTS = 'model-variants',
    PARAMETERS = 'parameters',
}

const MODEL_TABS_TO_PATH = {
    [ModelTabsKeys.LABELS]: paths.project.models.model.labels,
    [ModelTabsKeys.DATASETS]: paths.project.models.model.datasets,
    [ModelTabsKeys.STATISTICS]: paths.project.models.model.statistics,
    [ModelTabsKeys.MODEL_VARIANTS]: paths.project.models.model.modelVariants.index,
    [ModelTabsKeys.PARAMETERS]: paths.project.models.model.parameters,
};

const useGroupIsActiveLifecycle = (modelIdentifier: ModelIdentifier, modelGroup: ModelsGroups | undefined) => {
    const { data: supportedAlgorithms } = useSupportedAlgorithms(modelIdentifier);

    const group = supportedAlgorithms?.find(({ name }) => modelGroup?.groupName === name);

    return group?.lifecycleStage === LifecycleStage.ACTIVE;
};

const ProjectModel = (): JSX.Element => {
    const modelIdentifier = useModelIdentifier();
    const {
        project: { tasks },
    } = useProject();
    const navigate = useNavigate();
    const { useModelsGroupQuery } = useModels();
    const { modelDetails, ...rest } = useOptimizedModels();
    const { isLoading, data: modelGroup } = useModelsGroupQuery(modelIdentifier);
    const groupIsActiveLifecycle = useGroupIsActiveLifecycle(modelIdentifier, modelGroup);
    const match = useMatch(paths.project.models.model.index.path(':activeTab').pattern);

    const [isOverflowOn, setIsOverflowOn] = useState<boolean>(false);
    const [selectedModel, handleSelectModel] = useSelectedModel(modelGroup);

    if (modelGroup === undefined || selectedModel === undefined || modelDetails === undefined || isLoading) {
        return <Loading />;
    }

    const { modelTemplateId, taskId, groupName, modelTemplateName } = modelGroup;
    const name = `${modelGroup.modelTemplateName} (${groupName})`;
    const isLatestModel = selectedModel.version === modelGroup.modelVersions.at(0)?.version;

    const domain = tasks.find(({ id }) => modelGroup?.taskId === id)?.domain;
    const activeTab = match?.params.activeTab ?? ModelTabsKeys.MODEL_VARIANTS;

    // For visual prompt models we only have access to its pytorch model, the reference dataset and the labels
    // that were part of the reference dataset
    const VISUAL_PROMPT_ITEMS = [
        {
            id: 'model-variants-id',
            key: ModelTabsKeys.MODEL_VARIANTS,
            name: 'Model variants',
            children: (
                <PytorchTab
                    taskId={taskId}
                    groupName={groupName}
                    modelDetails={modelDetails}
                    modelTemplateName={modelTemplateName}
                    version={1}
                />
            ),
        },
        {
            id: 'training-datasets-id',
            key: ModelTabsKeys.DATASETS,
            name: 'Reference dataset',
            children: (
                <VisualPromptReferenceDataset
                    revisionId={modelDetails.trainingDatasetInfo.revisionId}
                    storageId={modelDetails.trainingDatasetInfo.storageId}
                    modelInformation={`${modelTemplateName} @ ${groupName} - ${getVersionWithDateText(
                        selectedModel.version,
                        selectedModel.creationDate
                    )}`}
                    modelLabels={modelDetails.labels}
                    taskId={taskId}
                    isActive={selectedModel.isActiveModel}
                />
            ),
        },
        {
            id: 'labels-id',
            key: ModelTabsKeys.LABELS,
            name: 'Labels',
            children: <ModelLabels labels={modelDetails.labels} domain={domain} />,
        },
    ];

    const ITEMS: TabItem[] = [
        {
            id: 'model-variants-id',
            key: ModelTabsKeys.MODEL_VARIANTS,
            name: 'Model variants',
            children: (
                <ModelVariants
                    modelDetails={modelDetails}
                    version={selectedModel.version}
                    modelTemplateName={modelTemplateName}
                    groupName={groupName}
                    taskId={taskId}
                    {...rest}
                />
            ),
        },
        {
            id: 'training-datasets-id',
            key: ModelTabsKeys.DATASETS,
            name: 'Training datasets',
            children: (
                <TrainingDataset
                    revisionId={modelDetails.trainingDatasetInfo.revisionId}
                    storageId={modelDetails.trainingDatasetInfo.storageId}
                    modelInformation={`${modelTemplateName} @ ${groupName} - ${getVersionWithDateText(
                        selectedModel.version,
                        selectedModel.creationDate
                    )}`}
                    modelLabels={modelDetails.labels}
                    taskId={taskId}
                    isActive={selectedModel.isActiveModel}
                />
            ),
        },
        {
            id: 'statistics-id',
            key: ModelTabsKeys.STATISTICS,
            name: 'Model metrics',
            children: <ModelStatistics />,
        },
        {
            id: 'configurable-parameters-id',
            key: ModelTabsKeys.PARAMETERS,
            name: 'Parameters',
            children: <ModelConfigurableParameters taskId={taskId} />,
        },
        {
            id: 'labels-id',
            key: ModelTabsKeys.LABELS,
            name: 'Labels',
            children: <ModelLabels labels={modelDetails.labels} domain={domain} />,
        },
    ];

    const handleSelectionChange = (key: Key): void => {
        navigate(MODEL_TABS_TO_PATH[key as ModelTabsKeys](modelIdentifier));

        setIsOverflowOn(key === ModelTabsKeys.MODEL_VARIANTS || key === ModelTabsKeys.LABELS);
    };

    const isVisualPromptingModel = isVisualPromptModelGroup(modelGroup);

    return (
        <PageLayout
            breadcrumbs={[
                {
                    id: 'models-id',
                    breadcrumb: 'Models',
                    href: paths.project.models.index({
                        organizationId: modelIdentifier.organizationId,
                        workspaceId: modelIdentifier.workspaceId,
                        projectId: modelIdentifier.projectId,
                    }),
                },
                {
                    id: `${idMatchingFormat(name)}-id`,
                    breadcrumb: (
                        <ModelBreadcrumb
                            handleSelectModel={handleSelectModel}
                            selectedModel={selectedModel}
                            modelGroup={modelGroup}
                            name={name}
                        />
                    ),
                },
            ]}
            header={
                <ModelCardMenu
                    model={selectedModel}
                    taskId={taskId}
                    isLatestModel={isLatestModel}
                    modelTemplateId={modelTemplateId}
                    projectIdentifier={modelIdentifier}
                    isMenuOptionsDisabled={!groupIsActiveLifecycle}
                />
            }
        >
            <Flex direction={'column'} height={'100%'}>
                <Flex direction={'column'} height={'100%'} UNSAFE_className={classes.projectModelView}>
                    {isVisualPromptingModel && <VisualPromptModelBetaWarning />}

                    <Flex direction={'column'} minHeight={0} flex={1}>
                        <Tabs
                            minHeight={0}
                            aria-label={'Model details'}
                            items={isVisualPromptingModel ? VISUAL_PROMPT_ITEMS : ITEMS}
                            height={'100%'}
                            selectedKey={activeTab}
                            onSelectionChange={handleSelectionChange}
                            panelOverflowY={isOverflowOn ? 'auto' : 'hidden'}
                        />
                    </Flex>
                </Flex>
            </Flex>
        </PageLayout>
    );
};

export default ProjectModel;
