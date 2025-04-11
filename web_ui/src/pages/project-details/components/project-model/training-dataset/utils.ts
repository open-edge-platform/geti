// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { v4 as uuidV4 } from 'uuid';

import {
    AdvancedFilterOptions,
    SearchRuleField,
    SearchRuleOperator,
} from '../../../../../core/media/media-filter.interface';

export enum Subset {
    TRAINING = 'training',
    VALIDATION = 'validation',
    TESTING = 'testing',
}

export const getSubsetMediaFilter = (subsetType: Subset): AdvancedFilterOptions => {
    return {
        condition: 'and',
        rules: [
            {
                field: SearchRuleField.Subset,
                operator: SearchRuleOperator.Equal,
                id: uuidV4(),
                value: subsetType,
            },
        ],
    };
};
