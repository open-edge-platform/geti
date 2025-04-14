// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, renderHook } from '@testing-library/react';
import { useSearchParams } from 'react-router-dom';

import { useFilterSearchParam } from './use-filter-search-param.hook';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useSearchParams: jest.fn(),
}));

describe('useFilterSearchParam', () => {
    it('uses search parameters to store search options', () => {
        const searchParams = new URLSearchParams();
        const setSpy = jest.spyOn(searchParams, 'set');

        // Generated from { foo: 'bar' }
        const originalFilter = 'JTdCJUMyJUE4Zm9vJUMyJUE4JUMyJUE4YmFyJUMyJUE4JTdE';
        searchParams.set('filter', originalFilter);

        const setSearchParams = jest.fn();

        jest.mocked(useSearchParams).mockImplementation(() => {
            return [searchParams, setSearchParams];
        });

        const { result } = renderHook(() => useFilterSearchParam('filter'));
        expect(result.current[0]).toEqual({ foo: 'bar' });

        act(() => {
            result.current[1]({ foo: 'baz' });
        });

        expect(setSearchParams).toHaveBeenCalled();
        expect(setSearchParams).toHaveBeenCalledWith(searchParams);
        expect(searchParams.get('filter')).not.toBe(originalFilter);
        expect(setSpy).toHaveBeenCalledWith('filter', 'JTdCJUMyJUE4Zm9vJUMyJUE4JUMyJUE4YmF6JUMyJUE4JTdE');
    });

    it('ignores invalid filters', () => {
        const searchParams = new URLSearchParams();

        const originalFilter = 'some-invalid-filter';
        searchParams.set('filter', originalFilter);

        const setSearchParams = jest.fn();

        jest.mocked(useSearchParams).mockImplementation(() => {
            return [searchParams, setSearchParams];
        });

        const { result } = renderHook(() => useFilterSearchParam('filter'));
        expect(result.current[0]).toEqual({});
    });
});
