// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { ModelFormat } from '../../../../../../core/models/dtos/model-details.interface';
import { OptimizedModel } from '../../../../../../core/models/optimized-models.interface';
import { getMockedOptimizedModel } from '../../../../../../test-utils/mocked-items-factory/mocked-model';
import { PreselectedModel } from '../../../../project-details.interface';
import { OptimizedModelsProps } from '../../hooks/use-optimized-models/use-optimized-models.hook.interface';
import { OptimizedModelTab } from './optimized-model-tab.component';
import { isNotBaselineModel } from './uitls';
import { useOpenVinoColumns } from './use-open-vino-columns.hook';

interface OpenvinoTabModelsProps extends Omit<OptimizedModelsProps, 'modelDetails'> {
    emptyModelMessage?: string;
    models: OptimizedModel[];
    isModelDeleted: boolean;
}

export const OpenVinoTabModels: FC<OpenvinoTabModelsProps> = ({
    models,
    isPOTModel,
    isModelDeleted,
    modelTemplateName,
    areOptimizedModelsVisible,
    emptyModelMessage,
    groupName,
    version,
    taskId,
    refetchModels,
}) => {
    const [selectedModel, setSelectedModel] = useState<PreselectedModel | undefined>(undefined);
    const openVinoModels = models.filter((model) => model.modelFormat !== ModelFormat.ONNX);

    const firstOptimizedModel = openVinoModels.filter(isNotBaselineModel).at(0);

    const emptyPOTModel: OptimizedModel | undefined =
        firstOptimizedModel === undefined
            ? undefined
            : getMockedOptimizedModel({
                  modelName: firstOptimizedModel.modelName.replace(/FP.*/, 'INT8') ?? '',
                  optimizationType: 'POT',
                  hasExplainableAI: false,
                  modelSize: '',
                  accuracy: null,
                  version: firstOptimizedModel.version,
                  modelFormat: ModelFormat.OpenVINO,
                  precision: ['INT8'],
                  id: '',
                  labels: [],
                  modelStatus: 'NOT_READY',
                  creationDate: '',
                  optimizationMethods: [],
                  optimizationObjectives: {},
                  previousRevisionId: '',
                  previousTrainedRevisionId: '',
                  purge_info: undefined,
                  lifecycleStage: firstOptimizedModel.lifecycleStage,
              });

    const hasStartOptimizationButton = !isPOTModel && !isModelDeleted;
    const finalOpenVinoModels =
        hasStartOptimizationButton && emptyPOTModel !== undefined ? [...openVinoModels, emptyPOTModel] : openVinoModels;

    const getModelColumns = useOpenVinoColumns({
        taskId,
        version,
        refetchModels,
        groupName,
        modelTemplateName,
        setSelectedModel,
        isModelDeleted,
        hasStartOptimizationButton,
    });

    return (
        <OptimizedModelTab
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
            columns={getModelColumns}
            models={finalOpenVinoModels}
            areOptimizedModelsVisible={areOptimizedModelsVisible}
            emptyModelMessage={emptyModelMessage}
            hasBaselineModels={true}
        />
    );
};
