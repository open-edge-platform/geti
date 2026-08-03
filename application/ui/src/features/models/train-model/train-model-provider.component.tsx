// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, Dispatch, ReactNode, SetStateAction, use, useMemo, useState } from 'react';

import type {
    DatasetRevision,
    Model,
    ModelArchitectureWithPerformanceCategory,
    TrainingConfiguration,
    TrainingDevice,
} from '@/api/types';
import { useGetDatasetRevisions } from 'hooks/use-get-dataset-revisions.hook';

import { useGetTaskModelArchitectures } from '../hooks/api/use-get-model-architectures.hook';
import { useGetSuccessfulModels } from '../hooks/api/use-get-models.hook';
import { useGetTrainingDevices } from './api/use-get-training-devices';
import { useTrainingConfiguration } from './hooks/use-training-configuration';
import { getDefaultTrainingDevice } from './select-training-device/utils';

type DatasetRevisionWithValue = Pick<DatasetRevision, 'id' | 'name'> & { value: string | null };
type InputWeightsWithValue = Pick<Model, 'id' | 'name' | 'architecture'> & { value: string | null };

export type TrainModelContextProps = {
    modelArchitectures: ModelArchitectureWithPerformanceCategory[];

    selectedModelArchitectureId: string | null;
    onSelectModelArchitectureId: (id: string | null) => void;

    trainingDevices: TrainingDevice[];
    selectedTrainingDevice: string | null;
    onSelectTrainingDevice: (deviceKey: string | null) => void;

    datasetRevisions: DatasetRevisionWithValue[];
    selectedDatasetRevisionId: string | null;
    onSelectDatasetRevisionId: (datasetRevision: string | null) => void;

    inputWeights: InputWeightsWithValue[];
    selectedInputWeightsId: string | null;
    onSelectInputWeightsId: (inputWeightsId: string | null) => void;

    isAdvancedSettingsMode: boolean;
    onToggleAdvancedSettingsMode: (isAdvancedSettingsMode: boolean) => void;

    trainingConfiguration: TrainingConfiguration | undefined;
    defaultTrainingConfiguration: TrainingConfiguration | undefined;
    onTrainingConfigurationChange: Dispatch<SetStateAction<TrainingConfiguration | undefined>>;

    showMoreModelArchitectures: boolean;
    onToggleShowMoreModelArchitectures: (showMore: boolean) => void;
};

const TrainModelContext = createContext<TrainModelContextProps | null>(null);

type TrainModelProviderProps = {
    children: ReactNode;
};

const useDatasetRevisions = () => {
    const { data: datasetRevisions } = useGetDatasetRevisions();

    return {
        datasetRevisions: [
            { id: 'use-current-dataset-revision', name: 'Use current dataset', value: null },
            ...(datasetRevisions?.map(({ id, name }) => ({ id, name, value: String(id) })) ?? []),
        ],
    };
};

const DEFAULT_PRE_TRAINED_WEIGHTS = 'default-pre-trained-weights';
const useInputWeights = () => {
    const { data: models } = useGetSuccessfulModels();

    return {
        inputWeights: [
            { id: DEFAULT_PRE_TRAINED_WEIGHTS, name: 'Default pre-trained weights', architecture: '', value: null },
            ...(models?.map(({ id, name, architecture }) => ({ id, name, architecture, value: String(id) })) ?? []),
        ],
    };
};

const getInputWeightsForArchitecture = (
    inputWeights: InputWeightsWithValue[],
    architectureId: string | null
): InputWeightsWithValue[] => {
    return inputWeights.filter((inputWeight) => {
        if (inputWeight.id === DEFAULT_PRE_TRAINED_WEIGHTS) {
            return true;
        }

        return inputWeight.architecture === architectureId;
    });
};

const getDefaultInputWeightsIdForArchitecture = (
    inputWeights: InputWeightsWithValue[],
    architectureId: string | null
): string | null => {
    const weightsForArchitecture = getInputWeightsForArchitecture(inputWeights, architectureId);
    const firstWeight = weightsForArchitecture.find(({ id }) => id !== DEFAULT_PRE_TRAINED_WEIGHTS);

    return firstWeight?.id ?? weightsForArchitecture.at(0)?.id ?? null;
};

export const createTrainingDeviceKey = (trainingDevice: TrainingDevice): string => {
    if (trainingDevice.index == null) {
        return trainingDevice.type;
    }

    return `${trainingDevice.type}-${trainingDevice.index}`;
};

export const TrainModelProvider = ({ children }: TrainModelProviderProps) => {
    const { modelArchitectures } = useGetTaskModelArchitectures();
    const { data: trainingDevices } = useGetTrainingDevices();
    const { datasetRevisions } = useDatasetRevisions();
    const { inputWeights: allInputWeights } = useInputWeights();

    const [selectedModelArchitectureId, setSelectedModelArchitectureId] = useState<string | null>(null);

    const [selectedTrainingDevice, setSelectedTrainingDevice] = useState<string | null>(() => {
        const defaultDevice = getDefaultTrainingDevice(trainingDevices);
        return defaultDevice ? createTrainingDeviceKey(defaultDevice) : null;
    });
    const [selectedDatasetRevisionId, setSelectedDatasetRevisionId] = useState<string | null>(
        datasetRevisions?.at(0)?.id ?? null
    );
    const [selectedInputWeightsId, setSelectedInputWeightsId] = useState<string | null>(() =>
        getDefaultInputWeightsIdForArchitecture(allInputWeights, selectedModelArchitectureId)
    );

    const [isAdvancedSettingsMode, setIsAdvancedSettingsMode] = useState<boolean>(false);

    const inputWeights = useMemo(() => {
        return getInputWeightsForArchitecture(allInputWeights, selectedModelArchitectureId);
    }, [allInputWeights, selectedModelArchitectureId]);

    const selectedInputWeights = inputWeights.find((weight) => weight.id === selectedInputWeightsId);

    const [trainingConfiguration, setTrainingConfiguration, defaultTrainingConfiguration] = useTrainingConfiguration({
        modelArchitectureId: selectedModelArchitectureId,
        modelInputWeightsId: selectedInputWeights?.value ?? null,
    });

    const [showMoreModelArchitectures, setShowMoreModelArchitectures] = useState<boolean>(false);

    const onSelectModelArchitectureId = (modelArchitectureId: string | null) => {
        setSelectedModelArchitectureId(modelArchitectureId);
        setSelectedInputWeightsId(getDefaultInputWeightsIdForArchitecture(allInputWeights, modelArchitectureId));
    };

    return (
        <TrainModelContext
            value={{
                modelArchitectures,

                selectedModelArchitectureId,
                onSelectModelArchitectureId,

                trainingDevices,
                selectedTrainingDevice,
                onSelectTrainingDevice: setSelectedTrainingDevice,

                datasetRevisions,
                selectedDatasetRevisionId,
                onSelectDatasetRevisionId: setSelectedDatasetRevisionId,

                inputWeights,
                selectedInputWeightsId,
                onSelectInputWeightsId: setSelectedInputWeightsId,

                isAdvancedSettingsMode,
                onToggleAdvancedSettingsMode: setIsAdvancedSettingsMode,

                showMoreModelArchitectures,
                onToggleShowMoreModelArchitectures: setShowMoreModelArchitectures,

                trainingConfiguration,
                defaultTrainingConfiguration,
                onTrainingConfigurationChange: setTrainingConfiguration,
            }}
        >
            {children}
        </TrainModelContext>
    );
};

export const useTrainModelState = () => {
    const context = use(TrainModelContext);

    if (context === null) {
        throw new Error('useTrainModel must be used within a TrainModelProvider');
    }

    return context;
};
