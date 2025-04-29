// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { usePrevious } from './use-previous.hook';

describe('usePrevious', () => {
    it('returns the previously rendered value', () => {
        const { result, rerender } = renderHook(({ value }) => usePrevious(value), { initialProps: { value: 1 } });

        expect(result.current).toEqual(undefined);
        rerender({ value: 2 });
        expect(result.current).toEqual(1);
        rerender({ value: 2 });
        expect(result.current).toEqual(2);
    });
});
