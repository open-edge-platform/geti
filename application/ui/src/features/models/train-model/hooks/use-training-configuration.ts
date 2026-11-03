// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { TrainingConfiguration } from '@/api/types';
import { isEqual } from 'lodash-es';

import {
    useGetModelArchitectureTrainingConfiguration,
    useGetModelTrainingConfiguration,
} from '../../hooks/api/use-get-model-training-configuration.hook';

type useTrainingConfigurationProps = {
    modelArchitectureId: string | null;
    modelRevisionId: string | null;
};

export const useTrainingConfiguration = ({ modelArchitectureId, modelRevisionId }: useTrainingConfigurationProps) => {
    const modelArchitectureTrainingConfigurationQuery = useGetModelArchitectureTrainingConfiguration({
        modelArchitectureId,
        modelRevisionId,
    });

    const modelTrainingConfigurationQuery = useGetModelTrainingConfiguration(modelRevisionId);

    const [trainingConfiguration, setTrainingConfiguration] = useState<TrainingConfiguration | undefined>(undefined);

    const defaultTrainingConfiguration =
        modelRevisionId === null
            ? modelArchitectureTrainingConfigurationQuery.data
            : modelTrainingConfigurationQuery.data;

    const [previousTrainingConfiguration, setPreviousTrainingConfiguration] = useState<
        TrainingConfiguration | undefined
    >(undefined);

    if (!isEqual(previousTrainingConfiguration, defaultTrainingConfiguration)) {
        setPreviousTrainingConfiguration(defaultTrainingConfiguration);
        setTrainingConfiguration(defaultTrainingConfiguration);
    }

    return [trainingConfiguration, setTrainingConfiguration, defaultTrainingConfiguration] as const;
};
