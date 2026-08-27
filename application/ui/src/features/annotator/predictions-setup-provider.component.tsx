// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, ReactNode, useContext, useMemo, useState } from 'react';

import type { Model } from '@/api/types';
import { usePipeline } from 'hooks/api/pipeline.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { orderBy } from 'lodash-es';
import { useLocalStorage } from 'usehooks-ts';

import { useGetActiveModel } from '../models/hooks/api/use-get-active-model.hook';
import { useGetSuccessfulModels } from '../models/hooks/api/use-get-models.hook';
import { getAllModelsWithOpenVINOVariants, SelectableModel } from '../models/utils';

type PredictionsSetupContextProps = {
    selectableModels: SelectableModel[];
    selectedModelId: string | null;
    selectedModel: SelectableModel | undefined;
    changeSelectedModelId: (modelId: string | null) => void;

    selectedDevice: string;
    changeSelectedDevice: (device: string) => void;

    confidenceThreshold: number | null;
    changeConfidenceThreshold: (confidenceThreshold: number) => void;
};

const PredictionSetupContext = createContext<PredictionsSetupContextProps | null>(null);

const getLatestModel = (models: Model[]): string | null => {
    const sortedModels = orderBy(models, (model) => model.training_info.end_time, 'desc');

    return getAllModelsWithOpenVINOVariants(sortedModels).at(0)?.modelVariantId ?? null;
};

const useSelectedModelId = (models: Model[]) => {
    const projectId = useProjectIdentifier();
    const activeModel = useGetActiveModel();

    const selectableModels = useMemo(() => getAllModelsWithOpenVINOVariants(models), [models]);

    const defaultSelectedId =
        selectableModels.find((model) => model.modelVariantId === activeModel?.model_variant_id)?.modelVariantId ??
        getLatestModel(models);

    return useLocalStorage<string | null>(`${projectId}-model-variant-id`, defaultSelectedId);
};

// The threshold is a model specific parameter, so an edited value only applies to the model it was set for.
const useConfidenceThreshold = (selectedModel: SelectableModel | undefined) => {
    const [editedThreshold, setEditedThreshold] = useState<{ modelVariantId: string; value: number } | null>(null);

    const confidenceThreshold =
        editedThreshold !== null && editedThreshold.modelVariantId === selectedModel?.modelVariantId
            ? editedThreshold.value
            : (selectedModel?.optimalConfidenceThreshold ?? null);

    const changeConfidenceThreshold = (value: number) => {
        if (selectedModel === undefined) {
            return;
        }

        setEditedThreshold({ modelVariantId: selectedModel.modelVariantId, value });
    };

    return [confidenceThreshold, changeConfidenceThreshold] as const;
};

export const PredictionsSetupProvider = ({ children }: { children: ReactNode }) => {
    const { data: models } = useGetSuccessfulModels();

    const selectableModels = useMemo(() => getAllModelsWithOpenVINOVariants(models), [models]);

    const [selectedModelId, setSelectedModelId] = useSelectedModelId(models);

    const selectedModel = selectableModels.find((model) => model.modelVariantId === selectedModelId);

    const [confidenceThreshold, changeConfidenceThreshold] = useConfidenceThreshold(selectedModel);

    const { data: pipeline } = usePipeline();

    const [selectedDevice, setSelectedDevice] = useState<string>(pipeline.device);

    return (
        <PredictionSetupContext
            value={{
                selectedModelId,
                selectedModel,
                changeSelectedModelId: setSelectedModelId,
                selectableModels,
                selectedDevice,
                changeSelectedDevice: setSelectedDevice,
                confidenceThreshold,
                changeConfidenceThreshold,
            }}
        >
            {children}
        </PredictionSetupContext>
    );
};

export const usePredictionSetup = () => {
    const context = useContext(PredictionSetupContext);

    if (context === null) {
        throw new Error('usePredictionSetup was used outside of PredictionsSetupProvider');
    }

    return context;
};
