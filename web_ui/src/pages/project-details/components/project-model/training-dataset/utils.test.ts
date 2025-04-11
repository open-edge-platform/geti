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

import { getSubsetMediaFilter, Subset } from './utils';

jest.mock('uuid', () => ({
    ...jest.requireActual('uuid'),
    v4: jest.fn(),
}));

describe('getSubsetMediaFilter function', () => {
    it('Check filter object for testings subset', () => {
        expect(getSubsetMediaFilter(Subset.TESTING)).toStrictEqual({
            condition: 'and',
            rules: [
                {
                    field: 'SUBSET',
                    operator: 'EQUAL',
                    id: uuidV4(),
                    value: 'testing',
                },
            ],
        });
    });

    it('Check filter object for validation subset', () => {
        expect(getSubsetMediaFilter(Subset.VALIDATION)).toStrictEqual({
            condition: 'and',
            rules: [
                {
                    field: 'SUBSET',
                    operator: 'EQUAL',
                    id: uuidV4(),
                    value: 'validation',
                },
            ],
        });
    });

    it('Check filter object for training subset', () => {
        expect(getSubsetMediaFilter(Subset.TRAINING)).toStrictEqual({
            condition: 'and',
            rules: [
                {
                    field: 'SUBSET',
                    operator: 'EQUAL',
                    id: uuidV4(),
                    value: 'training',
                },
            ],
        });
    });
});
