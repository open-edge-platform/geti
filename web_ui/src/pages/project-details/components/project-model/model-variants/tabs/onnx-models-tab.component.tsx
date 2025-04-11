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

import { FC, useState } from 'react';

import { ModelFormat } from '../../../../../../core/models/dtos/model-details.interface';
import { OptimizedModel } from '../../../../../../core/models/optimized-models.interface';
import { PreselectedModel } from '../../../../project-details.interface';
import { OptimizedModelTab } from './optimized-model-tab.component';
import { useColumnsModel } from './use-columns-model.hook';

interface OnnxModelsTabProps {
    models: OptimizedModel[];
    isModelDeleted: boolean;
    modelTemplateName: string;
    version: number;
    areOptimizedModelsVisible: boolean;
    taskId: string;
    groupName: string;
}

export const OnnxModelsTab: FC<OnnxModelsTabProps> = ({
    models,
    isModelDeleted,
    modelTemplateName,
    areOptimizedModelsVisible,
    version,
    taskId,
    groupName,
}) => {
    const [selectedModel, setSelectedModel] = useState<PreselectedModel | undefined>(undefined);

    const onnxModels = models.filter((model) => model.modelFormat === ModelFormat.ONNX);

    const getModelColumns = useColumnsModel({
        taskId,
        version,
        groupName,
        modelTemplateName,
        setSelectedModel,
        hideMenu: isModelDeleted,
    });

    return (
        <OptimizedModelTab
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
            columns={getModelColumns}
            areOptimizedModelsVisible={areOptimizedModelsVisible}
            hasBaselineModels={false}
            emptyModelMessage='There are no models with ONNX type.'
            models={onnxModels}
        />
    );
};
