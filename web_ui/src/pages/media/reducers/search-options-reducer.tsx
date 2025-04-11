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

import { v4 as uuidv4 } from 'uuid';

import {
    AdvancedFilterOptions,
    SearchOptionsActions,
    SearchOptionsActionsType,
} from '../../../core/media/media-filter.interface';
import { hasDifferentId } from '../../../shared/utils';

const MAX_AMOUNT_OF_RULES = 20;

export const SearchOptionReducer = (
    state: AdvancedFilterOptions,
    action: SearchOptionsActions
): AdvancedFilterOptions => {
    switch (action.type) {
        case SearchOptionsActionsType.ADD: {
            const currentRules = state?.rules ?? [];
            if (currentRules.length < MAX_AMOUNT_OF_RULES) {
                return {
                    condition: state.condition,
                    rules: [...currentRules, { id: uuidv4(), value: '', operator: '', field: '' }],
                };
            }
            return state;
        }

        case SearchOptionsActionsType.UPDATE: {
            if (state?.rules) {
                return {
                    condition: state.condition,
                    rules: state.rules.map((rule) => (rule.id === action.id ? action.rule : rule)),
                };
            }
            return state;
        }

        case SearchOptionsActionsType.RESET: {
            if (state?.rules) {
                return {
                    condition: state.condition,
                    rules: state.rules.map((rule) => (rule.id === action.id ? { ...rule, value: '' } : rule)),
                };
            }
            return state;
        }

        case SearchOptionsActionsType.REMOVE: {
            if (state?.rules) {
                return {
                    condition: state.condition,
                    rules: state.rules.filter(hasDifferentId(action.id)),
                };
            }
            return state;
        }

        case SearchOptionsActionsType.UPDATE_ALL: {
            return { ...action.filterOptions };
        }

        case SearchOptionsActionsType.REMOVE_ALL: {
            return {};
        }

        default:
            return { ...state };
    }
};
