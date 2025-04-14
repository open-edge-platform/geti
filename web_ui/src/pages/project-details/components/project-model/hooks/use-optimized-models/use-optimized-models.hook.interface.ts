// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { QueryObserverResult } from '@tanstack/react-query';

import { ModelDetails } from '../../../../../../core/models/optimized-models.interface';

export interface UseOptimizedModels {
    areOptimizedModelsVisible: boolean;
    isPOTModel: boolean;
    modelDetails?: ModelDetails;
    refetchModels: () => Promise<QueryObserverResult>;
}

export interface OptimizedModelsProps extends Required<UseOptimizedModels> {
    groupName: string;
    modelTemplateName: string;
    taskId: string;
    version: number;
}
