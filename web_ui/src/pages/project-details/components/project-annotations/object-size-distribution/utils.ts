// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ObjectSizeDistribution } from '../../../../../core/statistics/services/dataset-statistics.interface';
import { DistributionLabels } from './objects-list/objects-list.interface';

export const getDistributionLabels = (objectSizeDistribution: ObjectSizeDistribution[]): DistributionLabels[] =>
    objectSizeDistribution.map(({ labelName, labelId, labelColor }) => ({
        id: labelId,
        name: labelName,
        color: labelColor,
    }));

export const NEAR_MEAN_TOOLTIP_MSG = 'Near mean shows objects which size is very common. Preferable for calculation.';
