// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty } from 'lodash-es';
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
