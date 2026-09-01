// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';

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

    const [storedModelId, setStoredModelId] = useLocalStorage<string | null>(
        `${projectId}-model-variant-id`,
        defaultSelectedId
    );

    return [storedModelId, setStoredModelId] as const;
};

export const PredictionsSetupProvider = ({ children }: { children: ReactNode }) => {
    const { data: models } = useGetSuccessfulModels();

    const selectableModels = useMemo(() => getAllModelsWithOpenVINOVariants(models), [models]);

    const [selectedModelId, setSelectedModelId] = useSelectedModelId(models);

    const selectedModel = selectableModels.find((model) => model.modelVariantId === selectedModelId);

    const [confidenceThreshold, setConfidenceThreshold] = useState<number | null>(
        selectedModel?.optimalConfidenceThreshold ?? null
    );

    // The threshold is a model specific parameter, so it always follows the selected model
    const changeSelectedModelId = useCallback(
        (modelId: string | null) => {
            setSelectedModelId(modelId);

            const newModel = selectableModels.find((model) => model.modelVariantId === modelId);

            setConfidenceThreshold(newModel?.optimalConfidenceThreshold ?? null);
        },
        [selectableModels, setSelectedModelId]
    );

    const singleModelId = selectableModels.length === 1 ? selectableModels[0].modelVariantId : null;

    // The stored id is only read on mount, so a model trained later in the session is not picked up on its own
    useEffect(() => {
        if (singleModelId !== null && singleModelId !== selectedModelId) {
            changeSelectedModelId(singleModelId);
        }
    }, [singleModelId, selectedModelId, changeSelectedModelId]);

    const { data: pipeline } = usePipeline();

    const [selectedDevice, setSelectedDevice] = useState<string>(pipeline.device);

    return (
        <PredictionSetupContext
            value={{
                selectedModelId,
                selectedModel,
                changeSelectedModelId,
                selectableModels,
                selectedDevice,
                changeSelectedDevice: setSelectedDevice,
                confidenceThreshold,
                changeConfidenceThreshold: setConfidenceThreshold,
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
