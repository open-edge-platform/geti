// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
