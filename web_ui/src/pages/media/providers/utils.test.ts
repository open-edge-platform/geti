// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AdvancedFilterOptions, SearchRuleField, SearchRuleOperator } from '../../../core/media/media-filter.interface';
import { getRequiredAnomalyFilters, mergeMediaFilters } from './utils';

describe('media provider utils', () => {
    it('getRequiredAnomalyFilters', () => {
        const id = '123';
        expect(getRequiredAnomalyFilters(id)).toEqual({
            condition: 'and',
            rules: [
                {
                    id: expect.anything(),
                    field: SearchRuleField.LabelId,
                    operator: SearchRuleOperator.In,
                    value: [id],
                },
            ],
        });
    });

    describe('mergeMediaFilters', () => {
        const requiredFilter: AdvancedFilterOptions = {
            condition: 'and',
            rules: [
                {
                    id: 'requiredFilter-id',
                    operator: SearchRuleOperator.In,
                    field: SearchRuleField.LabelId,
                    value: ['123'],
                },
            ],
        };

        const filter: AdvancedFilterOptions = {
            condition: 'and',
            rules: [{ id: 'filter-id', operator: '', field: '', value: null }],
        };

        it('should return required filters when filters are empty', () => {
            expect(mergeMediaFilters({}, requiredFilter)).toEqual(requiredFilter);
        });

        it('should return filters when required filters are empty', () => {
            expect(mergeMediaFilters(filter, {})).toEqual(filter);
        });

        it('should merged filters with not the same field', () => {
            expect(mergeMediaFilters(filter, requiredFilter)).toEqual({
                ...filter,
                rules: [...requiredFilter.rules, ...filter.rules],
            });
        });

        it('should merge filters with favour of required filters when field is present in both filters', () => {
            const filterWithCommonField: AdvancedFilterOptions = {
                condition: 'and',
                rules: [
                    {
                        id: 'filter-id',
                        operator: SearchRuleOperator.In,
                        field: SearchRuleField.LabelId,
                        value: ['234'],
                    },
                ],
            };

            expect(mergeMediaFilters(filterWithCommonField, requiredFilter)).toEqual({
                ...filterWithCommonField,
                rules: requiredFilter.rules,
            });
        });
    });
});
