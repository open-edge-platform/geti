// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ObjectSizeDistribution } from '../../../../../core/statistics/services/dataset-statistics.interface';
import { DistributionLabels } from './objects-list/objects-list.interface';

export const getDistributionLabels = (objectSizeDistribution: ObjectSizeDistribution[]): DistributionLabels[] =>
    objectSizeDistribution.map(({ labelName, labelId, labelColor }) => ({
        id: labelId,
        name: labelName,
        color: labelColor,
    }));

export const NEAR_MEAN_TOOLTIP_MSG = 'Near mean shows objects which size is very common. Preferable for calculation.';
