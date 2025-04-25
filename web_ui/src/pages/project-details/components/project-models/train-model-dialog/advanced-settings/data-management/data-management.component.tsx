// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { View } from '@adobe/react-spectrum';

import { ConfigurableParametersTaskChain } from '../../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { BalanceLabelsDistribution } from './balance-labels-distribution/balance-labels-distribution.component';
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
            <BalanceLabelsDistribution />
            <TrainingSubsets
                isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                onReshufflingSubsetsEnabledChange={onReshufflingSubsetsEnabledChange}
            />
            {tilingParameters !== undefined && <Tiling tilingParameters={tilingParameters} />}
        </View>
    );
};
