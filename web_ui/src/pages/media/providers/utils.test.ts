// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
