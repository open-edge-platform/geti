// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { View } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { TrainingConfiguration } from '../../../../../../../core/configurable-parameters/services/configuration.interface';
import { DataAugmentation } from './data-augmentation/data-augmentation.component';
import { Filters } from './filters/filters.component';
import { Tiling } from './tiling/tiling.component';
import { TrainingSubsets } from './training-subsets/training-subsets.component';

interface DataManagementProps {
    trainingConfiguration: TrainingConfiguration;
    onUpdateTrainingConfiguration: (
        updateFunction: (config: TrainingConfiguration | undefined) => TrainingConfiguration | undefined
    ) => void;
}

const getTilingParameters = (_configParameters: TrainingConfiguration) => {
    return undefined;
};

export const DataManagement: FC<DataManagementProps> = ({ trainingConfiguration, onUpdateTrainingConfiguration }) => {
    const tilingParameters = getTilingParameters(trainingConfiguration);

    return (
        <View>
            {/* Not supported in v1 of training flow revamp <BalanceLabelsDistribution /> */}
            <TrainingSubsets
                subsetsConfiguration={trainingConfiguration.datasetPreparation.subsetSplit}
                onUpdateTrainingConfiguration={onUpdateTrainingConfiguration}
            />
            {tilingParameters !== undefined && <Tiling tilingParameters={tilingParameters} />}
            {!isEmpty(trainingConfiguration.datasetPreparation.augmentation) && <DataAugmentation />}
            <Filters
                filtersConfiguration={trainingConfiguration.datasetPreparation.filtering}
                onUpdateTrainingConfiguration={onUpdateTrainingConfiguration}
            />
            {/* Not supported in v1 of training flow revamp <RemovingDuplicates /> */}
        </View>
    );
};
