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

import isEmpty from 'lodash/isEmpty';
import { v4 as uuidv4 } from 'uuid';

import { AdvancedFilterOptions, SearchRuleField, SearchRuleOperator } from '../../../core/media/media-filter.interface';

export const getRequiredAnomalyFilters = (labelId: string): AdvancedFilterOptions => ({
    condition: 'and',
    rules: [
        {
            id: uuidv4(),
            field: SearchRuleField.LabelId,
            operator: SearchRuleOperator.In,
            value: [labelId],
        },
    ],
});

export const mergeMediaFilters = (
    filters: AdvancedFilterOptions,
    requiredFilters: AdvancedFilterOptions
): AdvancedFilterOptions => {
    if (isEmpty(requiredFilters)) {
        return filters;
    }

    if (isEmpty(filters)) {
        return requiredFilters;
    }

    // We prioritize required filters over other filters
    const rules = filters.rules.filter((rule) => {
        return !requiredFilters.rules.some((requiredRule) => {
            return requiredRule.field === rule.field;
        });
    });

    return {
        condition: filters.condition,
        rules: [...requiredFilters.rules, ...rules],
    };
};
