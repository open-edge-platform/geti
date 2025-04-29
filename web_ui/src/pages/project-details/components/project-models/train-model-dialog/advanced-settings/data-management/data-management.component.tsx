// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { View } from '@adobe/react-spectrum';

import { BalanceLabelsDistribution } from './balance-labels-distribution/balance-labels-distribution.component';
import { TrainingSubsets } from './training-subsets/training-subsets.component';

interface DataManagementProps {
    isReshufflingSubsetsEnabled: boolean;
    onReshufflingSubsetsEnabledChange: (reshufflingSubsetsEnabled: boolean) => void;
}

export const DataManagement: FC<DataManagementProps> = ({
    isReshufflingSubsetsEnabled,
    onReshufflingSubsetsEnabledChange,
}) => {
    return (
        <View>
            <BalanceLabelsDistribution />
            <TrainingSubsets
                isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                onReshufflingSubsetsEnabledChange={onReshufflingSubsetsEnabledChange}
            />
        </View>
    );
};
