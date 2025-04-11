// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { act, renderHook } from '@testing-library/react';

import { useSortTable } from './use-sort-table.hook';

describe('useSortTable', () => {
    const setQueryOptions = jest.fn();
    const initialQueryOptions = {
        sortBy: 'createdAt',
        sortDirection: 'DESC',
    };

    afterEach(() => {
        jest.resetAllMocks();
    });

    it('should initialize with the provided query options', () => {
        const { result } = renderHook(() => useSortTable({ queryOptions: initialQueryOptions, setQueryOptions }));

        const [sortingOptions] = result.current;

        expect(sortingOptions).toEqual(initialQueryOptions);
    });

    it('should toggle sort direction from ASC to DESC', () => {
        const initialQueryOptionsAsc = {
            sortBy: 'secondName',
            sortDirection: 'ASC',
        };
        const { result } = renderHook(() => useSortTable({ queryOptions: initialQueryOptionsAsc, setQueryOptions }));

        const [, sort] = result.current;

        act(() => {
            sort({ sortBy: 'secondName', sortDirection: 'DESC' });
        });

        const [sortingOptions] = result.current;

        expect(sortingOptions.sortDirection).toBe('DESC');
        expect(setQueryOptions).toHaveBeenCalledWith({
            ...initialQueryOptionsAsc,
            sortBy: 'secondName',
            sortDirection: 'DESC',
        });
    });

    it('should toggle sort direction from DESC to ASC', () => {
        const initialQueryOptionsDesc = {
            sortBy: 'secondName',
            sortDirection: 'DESC',
        };

        const { result } = renderHook(() => useSortTable({ queryOptions: initialQueryOptionsDesc, setQueryOptions }));

        const [, sort] = result.current;

        act(() => {
            sort({ sortBy: 'secondName', sortDirection: 'ASC' });
        });

        const [sortingOptions] = result.current;

        expect(sortingOptions.sortDirection).toBe('ASC');
        expect(setQueryOptions).toHaveBeenCalledWith({
            ...initialQueryOptionsDesc,
            sortDirection: 'ASC',
        });
    });

    it('should set sort direction to ASC for a new column', () => {
        const { result } = renderHook(() => useSortTable({ queryOptions: initialQueryOptions, setQueryOptions }));

        const [, sort] = result.current;

        act(() => {
            sort({ sortBy: 'email', sortDirection: 'DESC' });
        });

        const [sortingOptions] = result.current;

        expect(sortingOptions.sortBy).toBe('email');
        expect(sortingOptions.sortDirection).toBe('DESC');
        expect(setQueryOptions).toHaveBeenCalledWith({
            ...initialQueryOptions,
            sortBy: 'email',
            sortDirection: 'DESC',
        });
    });
});
