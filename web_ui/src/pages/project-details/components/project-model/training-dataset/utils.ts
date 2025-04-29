// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
