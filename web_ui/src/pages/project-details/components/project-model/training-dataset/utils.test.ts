// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
