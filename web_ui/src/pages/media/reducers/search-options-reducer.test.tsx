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

import {
    AdvancedFilterOptions,
    SearchOptionsActionsType,
    SearchOptionsRule,
} from '../../../core/media/media-filter.interface';
import { SearchOptionReducer } from './search-options-reducer';

const getMockRule = (value = 'test1', id: string): SearchOptionsRule => ({
    id,
    field: '',
    operator: '',
    value,
});

describe('SearchOptionReducer', () => {
    const ruleOne = getMockRule('test1', '321');
    const ruleTwo = getMockRule('test2', '123');

    it('add', () => {
        const state = SearchOptionReducer({}, { type: SearchOptionsActionsType.ADD });
        expect(state.rules).toEqual([{ id: expect.anything(), field: '', operator: '', value: '' }]);
    });

    it('add with previous rules', () => {
        const state = SearchOptionReducer(
            { condition: 'and', rules: [ruleOne] },
            { type: SearchOptionsActionsType.ADD }
        );
        expect(state.rules).toEqual([ruleOne, { id: expect.anything(), field: '', operator: '', value: '' }]);
    });

    it('add more than 20 rules', () => {
        const twentyRules = Array.from({ length: 20 }).map((_, i) => getMockRule(`valuew-${i}`, '123'));
        const state = SearchOptionReducer(
            { condition: 'and', rules: twentyRules },
            { type: SearchOptionsActionsType.ADD }
        );
        expect(state.rules).toHaveLength(20);
    });

    it('update', () => {
        const state = SearchOptionReducer(
            {
                condition: 'and',
                rules: [ruleOne, ruleTwo],
            },
            {
                id: ruleOne.id,
                type: SearchOptionsActionsType.UPDATE,
                rule: { ...ruleOne, value: 'test3' },
            }
        );
        expect(state.rules).toEqual([{ ...ruleOne, value: 'test3' }, ruleTwo]);
    });

    it('update with empty rules', () => {
        const state = SearchOptionReducer(
            {},
            {
                id: '123',
                type: SearchOptionsActionsType.UPDATE,
                rule: { id: '213', field: '', operator: '', value: 'test3' },
            }
        );
        expect(state).toEqual({});
    });

    it('remove', () => {
        const state = SearchOptionReducer(
            {
                condition: 'and',
                rules: [ruleOne, ruleTwo],
            },
            { type: SearchOptionsActionsType.REMOVE, id: ruleOne.id }
        );
        expect(state.rules).toEqual([ruleTwo]);
    });

    it('remove with empty rules', () => {
        const state = SearchOptionReducer({}, { type: SearchOptionsActionsType.REMOVE, id: '123' });
        expect(state).toEqual({});
    });

    it('update all', () => {
        const newfilterOptions: AdvancedFilterOptions = {
            condition: 'and',
            rules: [getMockRule('test1', '123')],
        };

        const state = SearchOptionReducer(
            {
                condition: 'and',
                rules: [getMockRule('test2', '321')],
            },
            {
                type: SearchOptionsActionsType.UPDATE_ALL,
                filterOptions: newfilterOptions,
            }
        );
        expect(state).toEqual(newfilterOptions);
    });

    it('remove all', () => {
        const state = SearchOptionReducer(
            {
                condition: 'and',
                rules: [getMockRule('test1', '123'), getMockRule('test2', '321')],
            },
            { type: SearchOptionsActionsType.REMOVE_ALL }
        );

        expect(state).toEqual({});
    });

    it('keeps the rule and update its value to empty("")', () => {
        const state = SearchOptionReducer(
            {
                condition: 'and',
                rules: [ruleOne, ruleTwo],
            },
            {
                id: ruleOne.id,
                type: SearchOptionsActionsType.RESET,
            }
        );
        expect(state.rules).toEqual([{ ...ruleOne, value: '' }, ruleTwo]);
    });

    it('returns current state', () => {
        const state = SearchOptionReducer(
            {},
            {
                id: ruleOne.id,
                type: SearchOptionsActionsType.RESET,
            }
        );
        expect(state).toEqual({});
    });
});
