// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { View } from '@geti/ui';

import { ConfigurableParametersTaskChain } from '../../../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { DataAugmentation } from './data-augmentation/data-augmentation.component';
import { Filters } from './filters/filters.component';
import { Tiling } from './tiling/tiling.component';
import { TrainingSubsets } from './training-subsets/training-subsets.component';

interface DataManagementProps {
    isReshufflingSubsetsEnabled: boolean;
    onReshufflingSubsetsEnabledChange: (reshufflingSubsetsEnabled: boolean) => void;
    configParameters: ConfigurableParametersTaskChain;
}

const getTilingParameters = (configParameters: ConfigurableParametersTaskChain) => {
    return configParameters.components.find((component) => component.header === 'Tiling');
};

export const DataManagement: FC<DataManagementProps> = ({
    isReshufflingSubsetsEnabled,
    onReshufflingSubsetsEnabledChange,
    configParameters,
}) => {
    const tilingParameters = getTilingParameters(configParameters);

    return (
        <View>
            {/* Not supported in v1 of training flow revamp <BalanceLabelsDistribution /> */}
            <TrainingSubsets
                isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                onReshufflingSubsetsEnabledChange={onReshufflingSubsetsEnabledChange}
            />
            {tilingParameters !== undefined && <Tiling tilingParameters={tilingParameters} />}
            <DataAugmentation />
            <Filters />
            {/* Not supported in v1 of training flow revamp <RemovingDuplicates /> */}
        </View>
    );
};
