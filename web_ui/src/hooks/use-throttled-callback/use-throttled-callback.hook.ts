// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';

import type { DebouncedFunc } from 'lodash';
import throttle from 'lodash/throttle';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Callback = (...args: any[]) => void;

export const useThrottledCallback = (callback: Callback, delay: number): DebouncedFunc<Callback> => {
    const savedCallback = useRef(callback);

    useLayoutEffect(() => {
        savedCallback.current = callback;
    }, [callback]);

    const debouncedCallback = useMemo(() => {
        return throttle(savedCallback.current, delay, {
            leading: true,
            trailing: true,
        });
    }, [delay]);

    useEffect(() => {
        return () => {
            debouncedCallback.cancel();
        };
    }, [debouncedCallback]);

    return debouncedCallback;
};
