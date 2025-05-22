// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, renderHook } from '@testing-library/react';

import { SortDirection } from '../../core/shared/query-parameters';
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
            sort({ sortBy: 'secondName', sortDirection: SortDirection.DESC });
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
            sort({ sortBy: 'secondName', sortDirection: SortDirection.ASC });
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
            sort({ sortBy: 'email', sortDirection: SortDirection.DESC });
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
