// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key, useState } from 'react';

import { useMatch, useNavigate } from 'react-router-dom';

import { OnnxLogo, OpenVINOIcon, PyTorchLogo } from '../../../../../assets/images';
import { paths } from '../../../../../core/services/routes';
import { useModelIdentifier } from '../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { Tabs } from '../../../../../shared/components/tabs/tabs.component';
import { TabItem } from '../../../../../shared/components/tabs/tabs.interface';
import { isModelDeleted } from '../../../utils';
import { OptimizedModelsProps } from '../hooks/use-optimized-models/use-optimized-models.hook.interface';
import { OnnxModelsTab } from './tabs/onnx-models-tab.component';
import { OpenVinoTabModels } from './tabs/open-vino-tab-models.component';
import { PytorchTab } from './tabs/pytorch-tab.component';
import { MODEL_TABS_TO_PATH, ModelVariantTabsKeys } from './tabs/tabs.interface';

export type ModelVariantsProps = OptimizedModelsProps;

export const ModelVariants = ({
    isPOTModel,
    areOptimizedModelsVisible,
    modelTemplateName,
    modelDetails,
    refetchModels,
    groupName,
    taskId,
    version,
}: ModelVariantsProps): JSX.Element => {
    const navigate = useNavigate();
    const { workspaceId, projectId, groupId, modelId, organizationId } = useModelIdentifier();
    const match = useMatch(paths.project.models.model.modelVariants.index.path(':activeTab').pattern);
    const [activeTab, setActiveTab] = useState(() => match?.params.activeTab ?? ModelVariantTabsKeys.OPENVINO);

    const modelDeleted = isModelDeleted(modelDetails);

    const ITEMS: TabItem[] = [
        {
            id: 'openvino-id',
            key: ModelVariantTabsKeys.OPENVINO,
            name: <OpenVINOIcon />,
            children: (
                <OpenVinoTabModels
                    areOptimizedModelsVisible={areOptimizedModelsVisible}
                    taskId={taskId}
                    groupName={groupName}
                    isPOTModel={isPOTModel}
                    modelTemplateName={modelTemplateName}
                    refetchModels={refetchModels}
                    version={version}
                    emptyModelMessage='There are no models optimised. Start optimization to generate OpenVINO models.'
                    isModelDeleted={modelDeleted}
                    models={modelDetails.optimizedModels}
                />
            ),
        },
        {
            id: 'pytorch-id',
            key: ModelVariantTabsKeys.PYTORCH,
            name: <PyTorchLogo />,
            children: (
                <PytorchTab
                    taskId={taskId}
                    groupName={groupName}
                    modelDetails={modelDetails}
                    modelTemplateName={modelTemplateName}
                    version={version}
                />
            ),
        },
        {
            id: 'onnx-id',
            key: ModelVariantTabsKeys.ONNX,
            name: <OnnxLogo />,
            children: (
                <OnnxModelsTab
                    models={modelDetails.optimizedModels}
                    taskId={taskId}
                    groupName={groupName}
                    areOptimizedModelsVisible={areOptimizedModelsVisible}
                    version={version}
                    modelTemplateName={modelTemplateName}
                    isModelDeleted={modelDeleted}
                />
            ),
        },
    ];

    const handleSelectionChange = (key: Key): void => {
        const tabKey = key as ModelVariantTabsKeys;

        if (tabKey === activeTab) {
            return;
        }

        setActiveTab(tabKey);
        navigate(
            MODEL_TABS_TO_PATH[tabKey]({
                modelId,
                projectId,
                workspaceId,
                organizationId,
                groupId,
            })
        );
    };

    return (
        <Tabs
            hideSelectionBar
            minHeight={0}
            items={ITEMS}
            height={'100%'}
            selectedKey={activeTab}
            aria-label={'Model variant tabs'}
            onSelectionChange={handleSelectionChange}
        />
    );
};
