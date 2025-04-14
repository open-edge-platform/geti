// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useLayoutEffect, useRef } from 'react';

export function useInterval(callback: () => void, delay: number | null): void {
    const savedCallback = useRef(callback);

    useLayoutEffect(() => {
        savedCallback.current = callback;
    }, [callback]);

    // Set up the interval.
    useEffect(() => {
        if (delay === null) {
            return;
        }

        const interval = setInterval(() => savedCallback.current(), delay);

        return () => clearInterval(interval);
    }, [delay]);
}
