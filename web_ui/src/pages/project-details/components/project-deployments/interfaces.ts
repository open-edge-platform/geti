// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ModelsGroups } from '../../../../core/models/models.interface';
import { SelectableOptimizationType } from '../../project-details.interface';
import { ModelVersion } from '../project-models/models-container/model-card/model-card.interface';

export interface DeployModel {
    modelGroupId: string;
    versionId: string;
    optimisationId: string | undefined;
    modelId: string;
}

export type DeployModelByTask = Record<string /* taskId */, DeployModel>;

export interface ModelSelectionProps {
    models: ModelsGroups[];
    selectedModel: DeployModel;
    selectModel: (model: DeployModel) => void;
}

export interface ModelConfiguration {
    selectedVersionId: string;
    selectedModelVersion: ModelVersion;
    selectedModelGroup: ModelsGroups;
    selectedOptimizationType: SelectableOptimizationType;
}
