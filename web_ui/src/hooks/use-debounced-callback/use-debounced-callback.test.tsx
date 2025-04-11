// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { act, renderHook } from '@testing-library/react';

import { useDebouncedCallback } from './use-debounced-callback.hook';

describe('useDebouncedCallback', () => {
    it('executes a given callback after given delay', () => {
        jest.useFakeTimers();

        const mockCallback = jest.fn();
        const delay = 1000;
        const { result } = renderHook(() => useDebouncedCallback(mockCallback, delay));

        const debouncedCallback = result.current;

        act(() => {
            debouncedCallback();
        });

        expect(mockCallback).toBeCalledTimes(0);

        jest.advanceTimersByTime(delay);

        expect(mockCallback).toBeCalledTimes(1);

        jest.clearAllTimers();
    });
});
