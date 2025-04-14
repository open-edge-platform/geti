// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, renderHook } from '@testing-library/react';

import { useRenderDelay } from './use-render-delay.hook';

describe('useRenderDelay', () => {
    it('given 0 as delay, it will return isShown as true', () => {
        const { result } = renderHook(() => useRenderDelay(0));

        expect(result.current).toEqual(true);
    });

    it('given X as delay, it will return isShown as true after X miliseconds', () => {
        jest.useFakeTimers();

        const { result } = renderHook(() => useRenderDelay(1000));

        expect(result.current).toEqual(false);

        act(() => {
            jest.advanceTimersByTime(1000);
        });

        expect(result.current).toEqual(true);

        jest.clearAllTimers();
        jest.useRealTimers();
    });
});
